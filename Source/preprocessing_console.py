import argparse
import sys
import csv

def getcolumnsIndex(data, columnsListString):
    columnsList = list()
    columnsListString = columnsListString.lstrip('{').rstrip('}')
    # Tách tên các thuộc tính từ string của argument columns được nhập vào
    columnsListStringSplited = columnsListString.split(',')
    # Lấy index của các thuộc tính này trong data
    try:
        for columns in columnsListStringSplited:
            columnsList.append(data[0].index(columns))
    except ValueError:
        print('No such columns')
        sys.exit()
    return columnsList

def minMaxNorm(data, args): # Chuẩn hóa các thuộc tính bằng phương pháp min-max
    # Lấy index của các thuộc tính được chọn
    columnsList = getcolumnsIndex(data, ','.join(args.columns))
    # Chuyển vị data để thuận tiện xử lý
    data = [[row[i] for row in data] for i in range(len(data[0]))]
    # Tham số newMin, newMax
    newMin, newMax = [eval(x) for x in args.newMinMax]
    # Với mỗi thuộc tính, tìm min và max, thực hiện mapping qua phép ánh xạ f(x)
    for columns in columnsList:
        oldMin, oldMax = min(data[columns][1:]), max(data[columns][1:])
        f = lambda x: (x - oldMin) / (oldMax - oldMin) * (newMax - newMin) + newMin
        data[columns][1:] = list(map(f, data[columns][1:]))
    # Chuyển vị lại data ban đầu
    data = [[row[i] for row in data] for i in range(len(data[0]))]
    return data

def zScoreNorm(data, args): # Chuẩn hóa các thuộc tính bằng phương pháp Z-score
    # Lấy index của các thuộc tính được chọn
    columnsList = getcolumnsIndex(data, ','.join(args.columns))
    # Chuyển vị data để thuận tiện xử lý
    data = [[row[i] for row in data] for i in range(len(data[0]))]
    # Với mỗi thuộc tính, tính mean và deviation, thực hiện mapping qua phép ánh xạ f(x)
    for columns in columnsList:
        mean = sum(data[columns][1:]) / (len(data[columns]) - 1)
        deviant = 0
        for v in range(len(data[columns]) - 1):
            deviant += abs(data[columns][v + 1] - mean)
        deviant /= len(data[columns]) - 1
        f = lambda x: (x - mean) / deviant
        data[columns][1:] = list(map(f, data[columns][1:]))
    # Chuyển vị lại data ban đầu
    data = [[row[i] for row in data] for i in range(len(data[0]))]
    return data

def missingValueRow(data,args): # Đếm số dong bị thiếu dữ liệu
    d = 0
    for i in range(len(data)):
        for j in range(len(data[0])):
            if data[i][j] == '':
                d += 1
                break
    print("Số dòng bị thiếu dữ liệu: ",d)
    return data

def missingValueColumns(data,args): #Liệt kê các cột bị thiếu dữ liệu
    l = list()
    columnName = list()
    for i in range(len(data)):
        for j in range(len(data[0])):
            if j not in l:
                if data[i][j] == '':
                    l.append(j)
    for i in l:
        columnName.append(data[0][i])
    print("các cột bị thiếu dữ liệu: ", columnName)
    return data

def delete_row(data,args): # Xóa các dòng bị thiếu dữ liệu với ngưỡng tỉ lệ thiếu (ratio) cho trước
    pData = list()
    for i in range(len(data)):
        d = 0
        for j in range(len(data[0])):
            if data[i][j] == '':
                d += 1
        if (d < len(data[0])*int(args.ratio)/100): # Nếu bị thiếu ít hơn 'ratio'% giá trị các thuộc tính thì không xóa
            pData += [data[i]]
    return pData

def delete_columns(data,args): # Xóa các cột bị thiếu dữ liệu với ngưỡng tỉ lệ thiếu (ratio) cho trước
    pData = list()
    l = list() # l là list các cột không bị xóa
    for i in range(len(data[0])):
        d = 0
        for j in range(len(data)):
            if data[j][i] == '':
                d += 1
        if (d < len(data)*int(args.ratio)/100): # Nếu bị thiếu ít hơn 'ratio'% số mẫu thì không xóa
            l.append(i)
    for i in range(len(data)):
        temp = list()
        for j in range(len(data[0])):
            if j in l:
                temp.append(data[i][j])
        pData += [temp]
    # print(l)
    return pData

def duplicateRow(data,args): # Xóa các mẫu bị trùng lặp
    pData = list()
    for i in range(len(data) - 1):
        if [data[i]] not in [data[j] for j in range(1,len(data))]: # Nếu dòng không bị trùng lặp thì thêm vào pData
            pData += [data[i]]
    # print(len(pData))
    return pData

def remove(data, args):
    # Lấy index của các thuộc tính được chọn
    columnsList = getcolumnsIndex(data, ','.join(args.columns))
    # Với mỗi thuộc tính, instance nào không bị trống thuộc tính này (nghĩa là instance hợp lệ) thì được copy vào biến pData
    pData = list()
    for columns in columnsList:
        pData = [data[0]]
        for inst in range(len(data) - 1):
            if data[inst + 1][columns] not in ['', []]:
                pData += [data[inst + 1]]
        data = pData
    return pData

def impute(data, args): # Điền các giá trị bị thiếu
    # Lấy index của các thuộc tính được chọn
    columnsList = getcolumnsIndex(data, ','.join(args.columns))
    # Với mỗi thuộc tính, tính mean (đối với kiểu numeric) hoặc mode (đối với kiểu categorical)
    pData = remove(data, args)
    pData = [[row[i] for row in pData] for i in range(len(pData[0]))]
    for columns in columnsList:
        try:
            # Thuộc tính numeric
            mean = sum(pData[columns][1:]) / (len(pData[columns]) - 1)
            for inst in range(len(data) - 1):
                if data[inst + 1][columns] in ['', []]:
                    data[inst + 1][columns] = mean
        except TypeError:
            # Thuộc tính non-numeric
            count = [[pData[columns][1:].count(value), value] for value in set(pData[columns][1:])]
            count.sort()
            for inst in range(len(data) - 1):
                if data[inst + 1][columns] in ['', []]:
                    data[inst + 1][columns] = count[-1][1]
    return data

def main():
    # Tham số dòng lệnh
    parser = argparse.ArgumentParser(description = 'Data preprocessing')
    parser.add_argument('--input', help = 'path to input file', required = True)
    parser.add_argument('--output', help = 'path to output file')
    parser.add_argument('--task', help = 'preprocessing task', required = True)
    parser.add_argument('--columns', help = 'thuộc tính list', nargs = '*')
    parser.add_argument('--newMinMax', help = 'new min and max for min-max normalization', nargs = 2)
    parser.add_argument('--ratio', help = 'ngưỡng tỉ lệ thiếu theo %')
    args = parser.parse_args()

    data = list()
    # Mở file input
    try:
        fint = open(args.input, 'r', encoding = 'utf-8-sig')
    except Exception:
        print('No such files or directories.')
        sys.exit()
    # Đọc dữ liệu vào biến data, chuyển chuỗi sang số
    for row in csv.reader(fint):
        for columns in range(len(row)):
            try:
                row[columns] = eval(row[columns])
            except Exception:
                pass
        data += [row]
    fint.close()

    # Xử lý
    switcher = {'missingValueRow': missingValueRow, 'missingValueColumns': missingValueColumns, 'impute': impute, 'delete_row': delete_row, 'delete_columns': delete_columns, 'duplicateRow': duplicateRow, 'minMaxNorm': minMaxNorm, 'zScoreNorm': zScoreNorm, 'remove': remove}
    func = switcher.get(args.task, lambda a1, a2: [])
    try:
        data = func(data, args)
    except TypeError:
        print('Some columns are empty or not numerical, or maybe not enough argument in command !')
        sys.exit()
    if data == []:
        print('Unknown task.')
        sys.exit()

    # Ghi data ra file output và đóng file
    if args.output != None:
        fout = open(args.output, 'w', encoding = 'utf-8-sig', newline = '')
        csv.writer(fout).writerows(data)
        fout.close()
    print("Task done!")
    return

main()