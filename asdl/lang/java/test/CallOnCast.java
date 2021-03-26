class A {
    int f() {
        A y = new A();
        ((A) y).g();
        return 0;
    }
    int g() {return 0;}
}

