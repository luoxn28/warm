import os


# markdown图片地址转换器，用于在github上正确展示图片地址用


def img_url_convert(path):
    change_flag = False
    change_list = []
    with open(path) as lines:
        for line in lines:
            pure_line = line.strip()
            if pure_line.startswith('![') and pure_line.endswith(')') and ('](' in pure_line):
                change_flag = True
                pure_line = '<img src="./' + pure_line[pure_line.rindex('(') + 1:pure_line.rindex(')')] + '"/>\n'
                change_list.append(pure_line)
            else:
                change_list.append(line)
    return change_flag, change_list


def save_file_if_img_url_convert(path):
    change, change_list = img_url_convert(path)
    if change:
        print(path + ' 有待转换的url，开始保存新文件')
        with open(path, 'w') as wfile:
            wfile.writelines(change_list)
        print(path + ' 保存成功')


for root, dirs, files in os.walk('./'):
    for file in files:
        if file.endswith('.md'):
            save_file_if_img_url_convert(os.path.join(root, file))
