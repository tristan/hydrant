public class Test {
	private Test() {
	}

	public static void test() {
		System.out.println("test!");
		System.out.println(_int);
		Float f = 1.0f;
		f.compareTo(2.0f);
		java.lang.Class c;
		System.out.println("BLAH:::::" + f + " :: ")
	}

	private static int _int = 0;

	static {
		_int = 2;
	}
}
