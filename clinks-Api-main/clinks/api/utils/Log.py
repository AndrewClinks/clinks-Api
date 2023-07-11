import os


def create(text, enabled_in_CI=False):
    if "CI" in os.environ and os.environ['CI'] == "true" and enabled_in_CI is False:
        return

    print(text)