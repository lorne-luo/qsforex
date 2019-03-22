def format_dict(d):
    ret_str = ''
    para_list = sorted(d.keys())
    for para in para_list:
        ret_str += '{:18}{}\n'.format(para + ':', d[para])
    return ret_str
