
package com.dtmilano.android.viewclient;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URLDecoder;
import java.util.ArrayList;
import java.util.StringTokenizer;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.zip.ZipException;

public class ViewClient {

    private static final boolean DEBUG = false;

    private static final String PROGNAME = "java -jar androidviewclient.jar";

    private static final String MONKEYRUNNER = "monkeyrunner";

    private static final int DELAY = 500;

    /**
     * The <em>tools</em> directory in the jar.
     */
    private static final String TOOLS = "tools";

    private enum Command {
        DUMP, CULEBRA
    };

    private volatile boolean mProcessFinished = false;

    /**
     * The destination file as command is extracted from jar.
     */
    private File mDest = null;

    private boolean mIsDestCreated = false;

    private boolean mKeep = false;

    /**
     * Command arguments.
     */
    private String[] mArgs = null;

    private JarFile mJar;

    /**
     * @author diego
     */
    private abstract class StreamReaderThread extends Thread {
        private InputStream mIs;
        private OutputStream mOs;

        /**
         * @param is
         * @param os
         */
        public StreamReaderThread(InputStream is, OutputStream os) {
            this.mIs = is;
            this.mOs = os;
        }

        /*
         * (non-Javadoc)
         * @see java.lang.Thread#run()
         */
        @Override
        public void run() {
            do {
                try {
                    while (mIs.available() > 0) {
                        mOs.write(mIs.read());
                    }
                } catch (IOException e) {
                    e.printStackTrace();
                } finally {
                    try {
                        Thread.sleep(DELAY);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
            } while (!mProcessFinished);
        }
    }

    /**
     * @author diego
     */
    private class OutputStreamReaderThread extends StreamReaderThread {

        /**
         * @param is
         * @param os
         */
        public OutputStreamReaderThread(InputStream is) {
            super(is, System.out);
        }

    }

    /**
     * @author diego
     */
    private class ErrorStreamReaderThread extends StreamReaderThread {

        /**
         * @param is
         * @param os
         */
        public ErrorStreamReaderThread(InputStream is) {
            super(is, System.err);
        }

    }

    /**
     * <em>ViewClient</em>
     * 
     * @throws IOException
     */
    public ViewClient(Command cmd, String[] args) throws IOException {
        if (args != null && args.length > 0) {
            mArgs = args;
        }
        final File file = new File(URLDecoder.decode(ViewClient.class.getProtectionDomain()
                .getCodeSource()
                .getLocation().getPath(), "UTF-8"));
        if (DEBUG) {
            System.err.println("jar=" + file.getCanonicalPath() + "    exists? " + file.exists());
        }

        try {
            mJar = new JarFile(file);
        } catch (ZipException e) {
            error("Tools should be started using the jar file.", e);
            usage();
        }

        final String entry = TOOLS + "/" + cmd.name().toLowerCase();
        final JarEntry jarEntry = mJar.getJarEntry(entry);
        if (jarEntry != null) {
            final InputStream is = mJar.getInputStream(jarEntry);
            // We cannot use /tmp or similar because sometimes it's mounted
            // noexec
            mDest = new File(System.getProperty("user.home") + File.separator
                    + cmd.name().toLowerCase());
            final FileOutputStream fos = new java.io.FileOutputStream(mDest);
            while (is.available() > 0) {
                fos.write(is.read());
            }
            fos.close();
            is.close();
            mDest.setExecutable(true);
            mIsDestCreated = true;
            if (!mKeep) {
                mDest.deleteOnExit();
            }
        }
        else {
            fatal("Cannot extract " + entry + " from jar");
        }

    }

    /**
     * Executes the command in a separate process.
     * 
     * @return the exit value of the process
     * @throws IOException
     * @throws InterruptedException
     */
    public int execute() throws IOException, InterruptedException {
        if (!mIsDestCreated) {
            throw new IllegalStateException("Destination was not extracted successfully");
        }
        final Runtime runtime = Runtime.getRuntime();
        final ArrayList<String> cmdList = new ArrayList<String>();
        final String monkeyrunner = locateMonkeyRunner();
        if (monkeyrunner != null) {
            cmdList.add(monkeyrunner);
            cmdList.add("-plugin");
            cmdList.add(mJar.getName());
        }
        else {
            if (isWindows()) {
                fatal(String.format(
                        "%s was not found and %s does not support shebang in scripts. Aborting.",
                        MONKEYRUNNER, System.getProperty("os.name")));
            }
        }
        cmdList.add(mDest.getAbsolutePath());
        if (mArgs != null) {
            for (String arg : mArgs) {
                cmdList.add(arg);
            }
        }
        if (DEBUG) {
            System.err.println("executing: " + cmdList);
        }
        final Process process = runtime.exec(cmdList.toArray(new String[] {}));
        if (process != null) {
            mProcessFinished = false;
            new OutputStreamReaderThread(process.getInputStream()).start();
            new ErrorStreamReaderThread(process.getErrorStream()).start();
            process.waitFor();
            try {
                Thread.sleep(DELAY + 500);
            } catch (InterruptedException e) {
                // do nothing
            }
            mProcessFinished = true;
            if (DEBUG) {
                System.err.println("process=" + process + "    " + process.exitValue());
            }
            return process.exitValue();
        }

        throw new RuntimeException("Couldn't create process");
    }

    /**
     * @return
     */
    private static boolean isWindows() {
        final String os = System.getProperty("os.name");
        return os.toUpperCase().contains("WINDOWS");
    }

    /**
     * Locates <code>monkeyrunner</code> executable in path.
     * 
     * @return the absolute path of <code>monkeyrunner</code> or
     *         <code>null</code> if not found
     */
    private static String locateMonkeyRunner() {
        final StringTokenizer tokenizer = new StringTokenizer(System.getenv("PATH"),
                File.pathSeparator);
        while (tokenizer.hasMoreTokens()) {
            final String dir = tokenizer.nextToken();
            File monkeyrunner = new File(dir + File.separator + MONKEYRUNNER + (isWindows() ? ".bat" : ""));
            if (DEBUG) {
                System.err.println("searching for " + monkeyrunner + "    exist? " + monkeyrunner.exists());
            }
            if (monkeyrunner.exists()) {
                return monkeyrunner.getAbsolutePath();
            }
        }

        return null;
    }

    /**
     * Prints usage and exits.
     */
    private static void usage() {
        System.err.println(String.format("usage: %s COMMAND [OPTION]... [ARGS]...", PROGNAME));
        System.err.println("");
        System.err.println("Commands:");
        for (Command cmd : Command.values()) {
            System.err.println("  " + cmd.name().toLowerCase());
        }
        System.exit(1);
    }

    /**
     * Obtains the extra arguments in the command line (following command, which
     * is assumed to be in args[0]).
     * 
     * @param args the arguments
     * @return The string array obtained from the arguments
     */
    private static String[] obtainExtraArgs(String[] args) {
        if (args.length > 1) {
            final String[] extras = new String[args.length - 1];
            for (int i = 1; i < args.length; i++) {
                extras[i - 1] = args[i];
            }
            return extras;
        }
        return null;
    }

    private static void error(String msg) {
        System.err.print("ERROR: ");
        System.err.println(msg);
    }

    private void error(String msg, Exception e) {
        error(msg);
        e.printStackTrace(System.err);
    }

    private static void fatal(String msg) {
        error(msg);
        System.exit(1);
    }

    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length < 1) {
            usage();
        }

        final String cmdStr = args[0];
        final String[] extras = obtainExtraArgs(args);

        if (DEBUG) {
            System.err.println("main: cmd=" + cmdStr + "    extras=" + extras);
        }

        try {
            System.exit(new ViewClient(Command.valueOf(cmdStr.toUpperCase()), extras).execute());
        } catch (IllegalArgumentException e) {
            error("Unknown command: '" + cmdStr + "'");
            usage();
        }

    }
}
