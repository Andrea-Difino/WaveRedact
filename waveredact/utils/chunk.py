

class Chunker:

    def __init__(self, overlap: int = 20, batch_size: int = 100):
        if overlap > batch_size:
            raise ValueError("overlap must be lower than batch_size")
        self.overlap = overlap
        self.batch_size = batch_size

    def chunk_text(self, full_text: dict[int,str]) -> list[dict[int,str]]:
        step = self.batch_size - self.overlap
        items = list(full_text.items())
        chunks = []

        for i in range(0, len(items), step):
            chunk = dict(items[i : i + self.batch_size])
            chunks.append(chunk)

            if i + self.batch_size >= len(items):
                break

        return chunks