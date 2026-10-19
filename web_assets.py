"""Clear local web-asset failures without modifying files or review data."""


class WebAssetError(RuntimeError):
    pass


def read_asset(root, name):
    # Names are application constants, never request-supplied paths.
    try:
        return (root / name).read_bytes()
    except OSError as error:
        raise WebAssetError(
            f'Required web file unavailable: {name}.\n'
            'Check that the project folder has not been moved or renamed and the file is readable.\n'
            'If accidentally deleted, run this from the correct project repository:\n'
            f'git restore --source=HEAD --worktree -- {name}\n'
            'Then restart the server and reload the page. Review data is not reset by this check.\n'
        ) from error


def check_assets(root, names):
    for name in names:
        read_asset(root, name)
