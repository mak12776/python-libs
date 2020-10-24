# allocating memory as much as needed.
import cpp_fmt_header_generator

try:
    cpp_fmt_header_generator.main()
except cpp_fmt_header_generator.MainError as e:
    print(f'error: {e.args[0]}')

"""
main_check:
    if (index == len)
        return total;

    switch (fmt[index])
    {
    case '{':
        index += 1;
        goto left_curly_bracket;

    case '}':
        index += 1;
        goto right_curly_bracket;

    default:
        index += 1;
        goto main_check;
    }

right_curly_bracket:
    if ((index == len) || (fmt[index] != '}'))
    {
        set(fmt_num_t::SINGLE_RIGHT_CURLY_BRACKET, index - 1);
        constexpr size_t invalid_total = 0;
    }

left_curly_bracket:
"""

