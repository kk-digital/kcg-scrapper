from fire import Fire

from kemono import utils


class Command:
    def compress_output(self, jsonl_path: str) -> None:
        utils.compress_output(jsonl_path)


if __name__ == "__main__":
    Fire(Command)
