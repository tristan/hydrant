import edu.sdsc.grid.io.srb.SRBFile;
import edu.sdsc.grid.io.srb.SRBFileSystem;

public class Dodgy1 extends Dodgy {
	
	private SRBFile f;
	public Dodgy1() {
		try {
			SRBFile f = new SRBFile(new SRBFileSystem(), "blah");
		} catch (Exception e) {
			
		}
	}
	
	public SRBFile getf() {
		return f;
	}
}
