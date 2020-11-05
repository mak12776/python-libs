from huffman import CountDict


def safe_convert_count_dict(source: CountDict, target_size: int):
    try:
        data_size = len(next(iter(source.keys())))
    except StopIteration:
        raise ValueError('source dict is empty')
    if data_size == 0:
        raise ValueError('length of source data is zero')
    if target_size >= data_size:
        raise ValueError(f'invalid data size: {data_size}')
    if data_size % target_size:
        raise ValueError(f'can\'t convert from {data_size} to {target_size}')
    raise BaseException('incomplete code')
