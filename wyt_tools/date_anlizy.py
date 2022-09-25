with open('../result_csv/data1.csv', 'r', encoding='utf8')as f:
    lines = f.readlines()
    data_lines = []
    print(lines[1], lines[2])
    for index, value in enumerate(lines):
        if '空' in value and '开' in value:
            price = float(value.split(',')[6])
            try:
                next_value = lines[index + 1]
            except:
                continue
            if '多' in next_value and '平' in next_value:
                get_price = price - float(next_value.split(',')[6])
                print(get_price)
                data_lines.append(value.strip() + ',0\n')
                data_lines.append(next_value.strip() + f',{get_price}\n')
        elif '多' in value and '开' in value:
            price = float(value.split(',')[6])
            try:
                next_value = lines[index + 1]
            except:
                continue
            if '空' in next_value and '平' in next_value:
                get_price = float(next_value.split(',')[6]) - price
                print(get_price)
                data_lines.append(value.strip() + ',0\n')
                data_lines.append(next_value.strip() + f',{get_price}\n')
        else:
            if '空' not in value and '多' not in value and '开' not in value and '平' not in value:
                data_lines.append(value.strip() + ',0\n')
    with open('data1.csv', 'w', encoding='utf8')as ff:
        for line in data_lines:
            ff.write(line)
