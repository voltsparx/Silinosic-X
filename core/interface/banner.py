# ──────────────────────────────────────────────────────────────
# SPDX-License-Identifier: AAL
#
# Silinosic-X Intelligence Framework
# Copyright (c) 2026 voltsparx
#
# Author     : voltsparx
# Repository : https://github.com/voltsparx/Silinosic-X
# Contact    : voltsparx@gmail.com
# License    : See LICENSE file in the project root
#
# This file is part of Silinosic-X and is subject to the terms
# and conditions defined in the LICENSE file.
# ──────────────────────────────────────────────────────────────

from core.foundation.colors import Colors, c
from core.foundation.metadata import VERSION, VERSION_THEME


def show_banner(anonymity_status: str = "No Anonymization") -> None:
    banner_lines = (
        ("    _____ _ ___                  _           ", "_  __"),
        ("   / ___/(_) (_)___  ____  _____(_)____     ", "| |/ /"),
        ("   \\__ \\/ / / / __ \\/ __ \\/ ___/ / ___/_____", "|   /"),
        ("  ___/ / / / / / / / /_/ (__  ) / /__/_____", "/   |"),
        (" /____/_/_/_/_/ /_/\\____/____/_/\\___/     ", "/_/|_|"),
    )
    for silinosic_block, x_block in banner_lines:
        print(f"{c(f' {silinosic_block}', Colors.WHITE)}{c(x_block, Colors.EMBER)}")

    print(
        f"{c(f'                                                 v{VERSION} ', Colors.WHITE)}"
        f"{c(f'[{VERSION_THEME}]', Colors.EMBER)}"
    )
    print("⸺" * 63)
    print(c("Hybrid console lanes: profile | surface | fusion | OCR", Colors.WHITE))
    print(f"{c('Current Anonymity:', Colors.EMBER)} {c(anonymity_status, Colors.CYAN)}")


# [OLD BANNER]
# .d8888. d888888b db      d888888b d8b   db  .d88b.  .d8888. d888888b  .o88b.       db    db
# 88'  YP   `88'   88        `88'   888o  88 .8P  Y8. 88'  YP   `88'   d8P  Y8       `8b  d8'
# `8bo.      88    88         88    88V8o 88 88    88 `8bo.      88    8P             `8bd8'
#   `Y8b.    88    88         88    88 V8o88 88    88   `Y8b.    88    8b      C8888D .dPYb.
# db   8D   .88.   88booo.   .88.   88  V888 `8b  d8' db   8D   .88.   Y8b  d8       .8P  Y8.
# `8888Y' Y888888P Y88888P Y888888P VP   V8P  `Y88P'  `8888Y' Y888888P  `Y88P'       YP    YP
