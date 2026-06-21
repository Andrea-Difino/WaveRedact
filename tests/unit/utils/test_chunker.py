import pytest
from waveredact.utils.chunk import Chunker


class TestChunker:

    @pytest.fixture
    def get_default_chunker(self):
        return Chunker()
    
    @pytest.fixture
    def get_modified_chunker(self):
        return Chunker(5, 10)
    
    @pytest.fixture
    def get_text_dict(self):
        return {0:" My", 1:" Name", 2: " is", 3: " Mario", 4: " Rossi", 5 : " and" , 6 : " I" , 7: " live" , 8 : " in", 9: "Ushwaganda", 10: " with" , 11 : " my", 12 : " family"}
    
    def test_wrong_init(self):
        with pytest.raises(ValueError, match="overlap must be lower than batch_size"):
            Chunker(20, 10)

    
    def test_init(self, get_default_chunker):
        assert get_default_chunker.overlap == 20
        assert get_default_chunker.batch_size == 100

    def test_modified_init(self, get_modified_chunker):
        assert get_modified_chunker.overlap == 5
        assert get_modified_chunker.batch_size == 10

    def test_chunk_text(self, get_modified_chunker, get_text_dict):
        
        result = get_modified_chunker.chunk_text(get_text_dict)

        assert [{0:" My", 1:" Name", 2: " is", 3: " Mario", 4: " Rossi", 5 : " and" , 6 : " I" , 7: " live" , 8 : " in", 9: "Ushwaganda"}, {5: ' and', 6: ' I', 7: ' live', 8: ' in', 9: 'Ushwaganda', 10: ' with', 11: ' my', 12: ' family'}] == result