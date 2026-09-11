# 파이썬 연습.py

#클래스정의
class Person:
    #초기화 메서드
    def __init__(self)):
        self.name = "default name"
    def printInfo(self):
        print("My name is{0}".format(self.name))

#인스턴스 생성
p1 = Person()

#매서드호출
p1.printInfo()
