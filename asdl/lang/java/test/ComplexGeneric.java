class A {

    public static <T extends Object & Foo<? extends T>> T complexGenerics() {
        return null;
    }

}
