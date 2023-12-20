-----
I stopped being able to run the file hello_world.py by opening a console, and navigating to /usr/lib/timetagger/examples/python/1-Quickstart and running python3 hello_world.py . However, I can't get this to work from a conda environment. Additionally, Swabian's instructions say to use an ipython shell and run hello_world but still doesn't work.

I am very confused because the following directories all have _TimeTagger.cxx, _TimeTagger.h, TimeTagger.py, and _TimeTagger.so
* ~/miniconda3/envs/timetagger/lib/python3.10/site-packages 
* ~/miniconda3/envs/timetagger/lib/python3.1/site-packages
* ~/miniconda3/envs/timetagger/lib/python3.10
* ~/miniconda3/envs/timetagger/lib/python3.1
And the following directory has libTimeTagger.so 
* ~/miniconda3/envs/timetagger/lib.

This matches that the following directory has _TimeTagger.cxx, _TimeTagger.h, TimeTagger.py, and _TimeTagger.so
* /usr/lib/python3/dist-packages
and the following directory has libTimeTagger.so 
* /usr/lib

I think the problem is when I compiled the .so file I might have needed to use different flags when working with a conda environment. But not totally sure...

-----
s

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



