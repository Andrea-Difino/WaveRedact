

class Chunker:
    """
    Split the text into chunks using an overlap to prevent cutting off words at boundaries.

    Attributes:
        overlap         - Number of tokens to overlap between chunks
        batch_size      - Maximum number of tokens per chunk
    """

    def __init__(self, overlap: int = 20, batch_size: int = 100):
        if overlap > batch_size:
            raise ValueError("overlap must be lower than batch_size")
        self.overlap = overlap
        self.batch_size = batch_size

    def chunk_text(self, full_text: dict[int,str]) -> list[dict[int,str]]:
        """
        Divide the full text dictionary into smaller chunks.

        Params:
            full_text   - Dictionary mapping indices to words

        Return:
            List of chunk dictionaries mapping indices to words
        """
        step = self.batch_size - self.overlap
        items = list(full_text.items())
        chunks = []

        for i in range(0, len(items), step):
            chunk = dict(items[i : i + self.batch_size])
            chunks.append(chunk)

            if i + self.batch_size >= len(items):
                break

        return chunks