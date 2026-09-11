#함수정의
def add(a, b):
    return a + b

#함수사용
result = add(5, 3)
print(result)

#배열형식 연습
lst = ["사과", "바나나", "체리","복숭아"]
print(len(lst))

for fruit in lst:
    print(fruit)

#리스트에 값을 추가, 삭제
lst.append("포도")
print(lst) 
lst.remove("바나나")
print(lst)         

#tuple형식 - 한방에 입력과 출력을 하는 배열형태
tp = (100, 200, 300)
print(len(tp))  
print(type(tp))
for item in tp:
    print(item)

#함수정의
def time(a,b):
    return a+b, a*b
# 함수 호출
result = times(5, 3)
print(result)