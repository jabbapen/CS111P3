#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""simulate.py

Simulate the testing of our implementation of W23 COM SCI 111 Lab 3:
Hash Hash Hash.

USAGE: ./simulate.py --help
"""

import re
import subprocess
import sys
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from time import sleep
from typing import List

__author__ = "Vincent Lin"

RED = "\x1b[31m"
GREEN = "\x1b[32m"
MAGENTA = "\x1b[35m"
END = "\x1b[0m"

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

parser = ArgumentParser(
    prog=Path(sys.argv[0]).name,
    description="Simulate testing of the hash table tester."
)

parser.add_argument("-d", "--delay", metavar="SECS",
                    type=float, default=1.0,
                    help="delay in seconds between each trial (default 1.0).")
parser.add_argument("-n", "--num-trials", metavar="NUM",
                    type=int, default=3,
                    help="number of trials per -s value (default 3).")
parser.add_argument("-v", "--verbose", action="store_true",
                    help="show original output for each trial.")
parser.add_argument("num_entries_list", nargs="*", metavar="NUM_ENTRIES",
                    type=int, default=[25000],
                    help="-s values to use (default 25000).")


def run(script: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(script, shell=True, capture_output=True)


@dataclass
class TrialOutput:
    base_missing: int
    v1_missing: int
    v2_missing: int
    generation_time: int
    base_time: int
    v1_time: int
    v2_time: int

    OUTPUT_FULL_MATCHER: re.Pattern[str] = field(
        init=False, repr=False, default=re.compile(
            r"Generation: (?P<generation_time>[\d,]+) usec\n"
            r"Hash table base: (?P<base_time>[\d,]+) usec\n"
            r"  - (?P<base_missing>[\d,]+) missing\n"
            r"Hash table v1: (?P<v1_time>[\d,]+) usec\n"
            r"  - (?P<v1_missing>[\d,]+) missing\n"
            r"Hash table v2: (?P<v2_time>[\d,]+) usec\n"
            r"  - (?P<v2_missing>[\d,]+) missing\n"
        )
    )

    def is_correct(self) -> bool:
        return not any((self.base_missing, self.v1_missing, self.v2_missing))

    def is_performant(self) -> bool:
        return self.v2_time < (self.base_time / 3)

    @classmethod
    def from_output(cls, stdout: str) -> "TrialOutput":
        match = cls.OUTPUT_FULL_MATCHER.match(stdout)
        if match is None:
            raise ValueError("Could not parse tester output, aborting.")

        stats = {attr: int(value.replace(",", ""))
                 for attr, value in match.groupdict().items()}
        return cls(**stats)


@dataclass
class Trial:
    trial_num: int
    output: TrialOutput
    original: str
    correct: bool = field(init=False)
    performant: bool = field(init=False)

    def __post_init__(self) -> None:
        self.correct = not any((self.output.base_missing,
                                self.output.v1_missing,
                                self.output.v2_missing))
        self.performant = self.output.v2_time < (self.output.base_time / 3)

    @classmethod
    def from_command(cls, command: str, trial_num: int) -> "Trial":
        process = run(command)
        stdout = process.stdout.decode()
        result = TrialOutput.from_output(stdout)
        return cls(trial_num, result, stdout)


class TrialResult(str, Enum):
    INCORRECT = f"{MAGENTA}INCORRECT{END}"
    PASSED = f"{GREEN}PASSED{END}"
    FAILED = f"{RED}FAILED{END}"


class Simulation:
    def __init__(self, config: Namespace) -> None:
        self.delay: float = config.delay
        self.num_trials: int = config.num_trials
        self.verbose: bool = config.verbose
        self.num_entries_list: List[int] = config.num_entries_list

    def __enter__(self) -> "Simulation":
        assert self.get_num_cores() == 4
        run("make >/dev/null")
        assert Path("./hash-table-tester").exists()
        return self

    def __exit__(self, *exc_args) -> None:
        run("make clean >/dev/null")

    def get_num_cores(self) -> int:
        process = run("nproc")
        stdout = process.stdout.decode()
        return int(stdout)

    def write_now(self, text: str) -> None:
        print(text, end="", flush=True)

    def run(self) -> bool:
        print("./hash-table-tester -t 4")
        print()

        passed_list = []
        failed_list = []
        incorrect_list = []
        for num_entries in self.num_entries_list:
            result = self.run_trial_group(num_entries)
            if result == TrialResult.PASSED:
                passed_list.append(num_entries)
            elif result == TrialResult.FAILED:
                failed_list.append(num_entries)
            else:
                incorrect_list.append(num_entries)
        print()

        num_inputs = len(self.num_entries_list)
        num_passed = len(passed_list)
        num_failed = len(failed_list)
        num_incorrect = len(incorrect_list)

        print("="*50)
        print(f"{GREEN}PASSED: {num_passed}/{num_inputs} {passed_list}{END}")
        print(f"{RED}FAILED: {num_failed}/{num_inputs} {failed_list}{END}")
        print(f"{MAGENTA}INCORRECT: {num_incorrect}/{num_inputs} "
              f"{incorrect_list}{END}")
        print("="*50)

        return num_incorrect == 0 and num_failed == 0

    def run_trial_group(self, num_entries: int) -> TrialResult:
        entries_prefix = f"-s {num_entries:6}: "
        if not self.verbose:
            self.write_now(entries_prefix)

        command = f"./hash-table-tester -t 4 -s {num_entries}"
        num_trial_passes = 0
        incorrect_found = False

        for trial_num in range(1, self.num_trials+1):
            trial = Trial.from_command(command, trial_num)

            mark = "?"  # Shouldn't be possible but yeah.
            if not trial.correct:
                incorrect_found = True
                mark = TrialResult.INCORRECT if self.verbose else "x"
            elif trial.performant:
                num_trial_passes += 1
                mark = TrialResult.PASSED if self.verbose else "."
            else:
                mark = TrialResult.FAILED if self.verbose else "F"

            if self.verbose:
                self.write_now(f"[{trial_num}/{self.num_trials}] ")
                self.write_now(entries_prefix)

            self.write_now(mark)

            if self.verbose:
                print()
                self.write_now(trial.original)
                self.show_offense(trial)
                print()

            sleep(self.delay)

        if incorrect_found:
            summary = TrialResult.INCORRECT
        elif num_trial_passes > 0:
            summary = TrialResult.PASSED
        else:
            summary = TrialResult.FAILED

        if self.verbose:
            print("-"*50)
            print(f"{entries_prefix}{summary.value}")
            print("-"*50)
            print()
        else:
            print(f" {summary.value}")

        return summary

    def show_offense(self, trial: Trial) -> None:
        if not trial.correct:
            base = trial.output.base_missing
            v1 = trial.output.v1_missing
            v2 = trial.output.v2_missing
            message = ", ".join(f"{ver}: {num} missing" for ver, num in
                                zip(("base, v1, v2"), (base, v1, v2))
                                if num > 0)
            print(f"{MAGENTA}{message}{END}")
        elif not trial.performant:
            ratio = trial.output.base_time / 3
            formula = f"{trial.output.v2_time} < {ratio:.2f}"
            print(f"{RED}{formula}{END}")


def main() -> int:
    namespace = parser.parse_args()

    with Simulation(namespace) as simulation:
        all_passed = simulation.run()

    if all_passed:
        return EXIT_SUCCESS
    return EXIT_FAILURE


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(EXIT_FAILURE)
