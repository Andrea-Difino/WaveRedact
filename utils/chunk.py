

class Chunker:

    def __init__(self, overlap: int = 20, batch_size: int = 100):
        self.overlap = overlap
        self.batch_size = batch_size

    def chunk_text(self, full_text: dict[int,str]) -> list[dict[int,str]]:

        step = self.batch_size - self.overlap
        chunks = [dict(list(full_text.items())[i:i + self.batch_size]) for i in range(0, len(full_text), step)]

        return chunks