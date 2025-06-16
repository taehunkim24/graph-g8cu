import it.unimi.dsi.webgraph.BVGraph;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.OutputStreamWriter;
import java.io.Writer;

public class DumpEdges {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("usage: java DumpEdges <basename.graph> <out.txt>");
            return;
        }
        String base = args[0].replaceAll("\\.graph$", "");
        String out  = args[1];

        BVGraph g = BVGraph.load(base);
        Writer w = out.equals("-") ?                  // "-" → stdout
                    new BufferedWriter(new OutputStreamWriter(System.out))
                  : new BufferedWriter(new FileWriter(out));

        for (int u = 0; u < g.numNodes(); u++) {
            int[] succ = g.successorArray(u);   // 필요 크기 자동 할당
            for (int v : succ)
                w.write(u + " " + v + "\n");
        }
        w.flush();
    }
}
