```
    def _count_ints(self, buffer: bytes):
        count_dict = defaultdict(lambda: 0)
        if self.data_bits == 8:
            for value in buffer:
                count_dict[value] += 1
            return count_dict, 0
        elif self.data_bits % 8 == 0:
            max_index = self.buffer_size - self.remaining_size
            for index in range(0, max_index, self.data_size):
                count_dict[_from_bytes(buffer[index:index + self.data_size])] += 1
            return count_dict, _from_bytes(buffer[max_index:])
        else:
            if self.buffer_bits < self.data_bits:
                return count_dict, _from_bytes(buffer)
            full_read_bits = self.data_size * 8
            residual_size = self.buffer_size % self.data_size

            # read first data bits
            read_value = _from_bytes(buffer[0: 0 + self.data_size])
            residual_bits = full_read_bits
            while residual_bits >= self.data_bits:
                residual_bits -= self.data_bits
                count_dict[read_value >> residual_bits] += 1
                read_value &= _mask(residual_bits)

            # read rest data bits
            max_index = self.buffer_size - residual_size
            index = self.data_size
            while index < max_index:
                # save value
                necessary_bits = self.data_bits - residual_bits
                saved_value = read_value << necessary_bits
                # read next
                read_value = _from_bytes(buffer[index: index + self.data_size])
                residual_bits = full_read_bits - necessary_bits
                count_dict[saved_value | (read_value >> residual_bits)] += 1
                read_value &= _mask(residual_bits)
                # remaining bits
                while residual_bits >= self.data_bits:
                    residual_bits -= self.data_bits
                    count_dict[read_value >> residual_bits] += 1
                    read_value &= _mask(residual_bits)
                # inc index
                index += self.data_size

            if residual_size:
                full_read_bits = self.remaining_size * 8
                read_value = (read_value << full_read_bits) | _from_bytes(buffer[max_index:])
                residual_bits += full_read_bits
                while residual_bits >= self.data_bits:
                    residual_bits -= self.data_bits
                    count_dict[read_value >> residual_bits] += 1
                    read_value &= _mask(residual_bits)
            return count_dict, read_value
```