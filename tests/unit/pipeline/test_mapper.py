from waveredact.pipeline.mapper import ChunkMapper
import pytest


class TestMapper:

    @pytest.fixture
    def get_chunks(self) -> dict[int, str]:
        return {0: " My", 1:" name", 2:" is", 3:" Mario", 4:" Rossi"}

    @pytest.fixture
    def get_mapper(self, get_chunks) -> ChunkMapper:
        return ChunkMapper(get_chunks)


    def test_build_mapping(self, get_mapper, get_chunks):
        mapper = get_mapper

        assert mapper.text == ' My name is Mario Rossi'
        assert mapper.char_mapping == {0: (0, 3), 1: (3, 8), 2: (8, 11), 3: (11, 17), 4: (17, 23)}
        assert mapper.chunk == get_chunks

    def test_get_original_idx(self, get_mapper, get_chunks):

        found_id = get_mapper.get_original_idxs(11,23)

        assert found_id == [3,4]
        assert get_chunks[found_id[0]] == ' Mario'
        assert get_chunks[found_id[1]] == ' Rossi'