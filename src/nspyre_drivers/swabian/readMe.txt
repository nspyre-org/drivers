-----

Summary:

Swabian provided us with Linux installation instructions (https://www.swabianinstruments.com/static/documentation/TimeTagger/sections/installation.html), python examples (/usr/lib/timetagger/examples/python), and the shared object file _TimeTagger.so which can be generated using _TimeTagger.cxx and _TimeTagger.h (in /usr/lib/python3/dist-packages)
	* NOTE: although not clearly specified in these Linux installation instructions, Swabian suggested using Anaconda, but this is meant only for Windows systems (they are going to improve the documentation in future releases)
* Create conda environment
* activate the environment
* install numpy
* open python within the environment and run "import sys; print(sys.path)". A list of the directories in sys.path should be printed. In one of the sys.path directories, for instance /home/exodia/.local/lib/python3.10/site-packages, copy the files _TimeTagger.cxx, _TimeTagger.h, TimeTagger.py, and _TimeTagger.so from /usr/lib/python3/dist-packages. 
* Compile the files. I created file script.sh in the directory I copied the time tagger files with the code from the Linux installation instructions
PYTHON_FLAGS="`python3-config --includes --libs`"
NUMPY_FLAGS="-I`python3 -c \"print(__import__('numpy').get_include())\"`"
TTFLAGS="-I/usr/include/timetagger -lTimeTagger"
CFLAGS="-std=c++17 -O2 -DNDEBUG -fPIC $PYTHON_FLAGS $NUMPY_FLAGS $TTFLAGS"

g++ -shared _TimeTagger.cxx $CFLAGS -o _TimeTagger.so
* Run the script: sudo bash script.sh . You will get some compiler warnings. Ignore them.
* Go to /usr/lib/timetagger/examples/python/1-Quickstart and run python hello_world.py. 
* May get an import error like this -- 
ImportError: /home/exodia/miniconda3/envs/timetagger/bin/../lib/libstdc++.so.6: version `GLIBCXX_3.4.30` not found (required by /home/exodia/miniconda3/envs/timetagger/bin/../lib/libTimeTagger.so) 

From Swabian:
This message tells that the version of libstdc++.so.6 shipped by Anaconda is older than the one shipped by Ubuntu 22.04.
This is the main C++ plattform library of the compiler, but luckily it supports great backwards compatibility.
However Anaconda seems to prefer its own version of this library.
We use the Ubuntu's one to compile libTimeTagger.so and so this defines the minimum version we require.
* Use conda to update this library. e.g. https://stackoverflow.com/questions/72540359/glibcxx-3-4-30-not-found-for-librosa-in-conda-virtual-environment-after-tryin explains some steps here. 

We ran: conda install -c conda-forge gcc=12.1.0

python hello_world.py -- worked for us.

* Now test that you can connect to the hardware
python /usr/lib/timetagger/examples/python/1-Quickstart/2-controlling-the-hardware/A_get_hardware_information.py 
Also worked for us. You can confirm by seeing the serial number of your time tagger printed out

-----
Some notes on my first time setting up the time tagger:

https://www.swabianinstruments.com/static/documentation/TimeTagger/sections/installation.html
See Linux installation instructions.
* Examples are in /usr/lib/timetagger/examples/python
* Found _TimeTagger.cxx, _TimeTagger.h, TimeTagger.py, and _TimeTagger.so in /usr/lib/python3/dist-packages

* Created conda environment timetagger conda create --name timetagger
* conda install numpy
* conda install matplotlib
* conda install ipython
* conda install python=3.10 (probably don't need to do this)
* Create file /usr/lib/python3/dist-packages/script.sh with contents
PYTHON_FLAGS="`python3-config --includes --libs`"
NUMPY_FLAGS="-I`python3 -c \"print(__import__('numpy').get_include())\"`"
TTFLAGS="-I/usr/include/timetagger -lTimeTagger"
CFLAGS="-std=c++17 -O2 -DNDEBUG -fPIC $PYTHON_FLAGS $NUMPY_FLAGS $TTFLAGS"

g++ -shared _TimeTagger.cxx $CFLAGS -o _TimeTagger.so
* Navigate to /usr/lib/python3/dist-packages/ and run sudo bash script.sh. Will get some warnings
* Outside of the conda environment go to /usr/lib/timetagger/examples/python/1-Quickstart and run python3 hello_world.py. Works!

* Now go back into the conda environment timetagger and navigate to ~/miniconda3/envs/timetagger/lib/python3.10
cp /usr/lib/python3/dist-packages/_TimeTagger.cxx .
cp /usr/lib/python3/dist-packages/_TimeTagger.h .
cp /usr/lib/python3/dist-packages/TimeTagger.py .
cp /usr/lib/python3/dist-packages/_TimeTagger.so .
* Navigate back to /usr/lib/timetagger/examples/python/1-Quickstart and run python hello_world.py
 --> seems like it is kinda working? Can import _TimeTagger

 * Now go back into the conda environment timetagger and navigate to ~/miniconda3/envs/timetagger/lib/python3.10/site-packages
 cp /usr/lib/python3/dist-packages/_TimeTagger.cxx .
cp /usr/lib/python3/dist-packages/_TimeTagger.h .
cp /usr/lib/python3/dist-packages/TimeTagger.py .
cp /usr/lib/python3/dist-packages/_TimeTagger.so .
* Navigate back to /usr/lib/timetagger/examples/python/1-Quickstart and run python hello_world.py

Go to ~/miniconda3/envs/timetagger/lib and cp /usr/lib/libTimeTagger.so .
ImportError: /home/exodia/miniconda3/envs/timetagger/bin/../lib/libstdc++.so.6: version `GLIBCXX_3.4.30' not found (required by /lib/libTimeTagger.so)

From Swabian:
This message tells that the version of libstdc++.so.6 shipped by Anaconda is older than the one shipped by Ubuntu 22.04.
This is the main C++ plattform library of the compiler, but luckily it supports great backwards compatibility.
However Anaconda seems to prefer its own version of this library.
We use the Ubuntu's one to compile libTimeTagger.so and so this defines the minimum version we require.
* Use conda to update this library. e.g. https://stackoverflow.com/questions/72540359/glibcxx-3-4-30-not-found-for-librosa-in-conda-virtual-environment-after-tryin explains some steps here. 

We ran: conda install -c conda-forge gcc=12.1.0

hello_world.py works