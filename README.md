# images_findpip

Finds pictures in pictures.

images_findpip.py is a python 3 script that can run as is, as a Docker container ([docker run](https://docs.docker.com/engine/reference/run/)), or as a Docker service ([docker service create](https://docs.docker.com/engine/reference/commandline/service_create/)).

Except for the special urls listed below, all output from this script must be redirected into a .tar.gz file. See the usage examples on how to redirect the output into a .tar.gz file.

## Requirements

Currently, all files to be processed by this script must be on a web server or ftp server.

### Running Standalone

You will need to install [opencv](http://www.opencv.org) 3.4.0, python-numpy, python-scipy and a bunch of other packages. Use the opencv_install.sh file to install opencv 3.4.0 and python3.5.

The package manager used by opencv_install.sh is apt-get which limits the script to computers running the Ubuntu or Debian OS.

After opencv has been successfully installed, simply run `python3.5 ./images_findpip.py`.

### Running In A Docker Container

You will need to [install Docker](https://docs.docker.com/engine/installation/) on at least one computer.

Once Docker has been installed, you can then build the Docker container and run it.

To build the container, run `docker build -t images_findpip .` in the folder that you downloaded the contents of this repository to. When the build is finished, you can start the container with `docker run -d -p 6003:6003 --network=host --name images_findpip images_findpip`

### Running As A Docker Service

You will need to [install Docker](https://docs.docker.com/engine/installation/) on at least two computers.

Once Docker has been installed on the computers, you can then build the Docker container and run it.

To build the container, run `docker build -t images_findpip .` in the folder that you downloaded the contents of this repository to. When the build is finished, you can start the container with `docker service create --replicas 2 --publish published=6003,target=6003 --name images_findpip images_findpip`

## Options

There are three options that can be passed to the script to affect the data it returns. Note that the options reset to default values between calls to the script.

Multiple options can be specified in each request by separating them with three asterisks (***).

Example: debugfileon***returncolor

These options will be ignored if using one of the special urls listed below.

### debugmodeoff

This option will turn off ALL debugging output. No data will be printed to the console or log file.

The script default is to turn debug mode on.

### debugfileon

Writes the debug log to a file named debug.txt which will be included in the .tar.gz file returned by the script.

The script default is not to include the debug.txt file.

### returncolor

If turned on, the pictures found by the script will be in color if the source image is in color.

Script default is to return grayscale (a.k.a black & white) pictures even if the source image is in color.

## Special URLs

Special URLs allow the client to retrieve a help/description file and the scripts version number. You do not need to redirect the scripts output when using these special URLs.

http://helpme  
Returns a text file containing instructions on how to use this script and the scripts version number.

http://version  
Returns a text file containing only the scripts version number

## Command Line Usage Examples

These examples will work with the script regardless of how you started `images_findpip.py`.

You can try to send multiple urls per request but only the first url found will be processed. All other urls will be ignored.

### Example 1

Return color pictures.

#### Command

`curl -d "http://www.example.com/testimage01_color.png***returncolor~~~" <server_ip_or_hostname>:6003 > ~/results.tar.gz`

#### Result

The pictures found in testimage01_color.png will be in color with the script output saved to `~/results.tar.gz`.

### Example 2

Return grayscale pictures.

#### Command

`curl -d "http://www.example.com/testimage01_color.png~~~" <server_ip_or_hostname>:6003 > ~/results.tar.gz`

#### Result

The pictures found in testimage01_color.png will be converted to grayscale with the script output saved to `~/results.tar.gz`.

### Example 3

Return grayscale pictures and the debug.txt file.

#### Command

`curl -d "http://www.example.com/testimage01_color.png***debugfileon~~~" <server_ip_or_hostname>:6003 > ~/results.tar.gz`

#### Result

The pictures found in `testimage01_color.png` will be converted to grayscale with the script output saved to `~/results.tar.gz`. Also included in results.tar.gz will be a file named `debug.txt` showing what functions the script ran to get the pictures that it found.

### Example 4

This is a valid request.

It demonstrates what happens when you include multiple urls, random characters and multiple options. Also note that some options have extra (more than 3) asterisks before and/or after them.

#### Command

`curl -d "abcd***http://www.example.com/some/folder/testimage01_color.png*****returncolor***http://www.example.com/testimage45.png****debugfileon***returncolor~~~" <server_ip_or_hostname>:6003 > ~/some/folder/somwhere/testimage01_color.tar.gz`

#### Result

The pictures found in `testimage01_color.png` will be in color. Also included in results.tar.gz will be a file named `debug.txt` showing what functions the script ran to get the pictures that it found. The scripts output will be saved to `~/some/folder/somwhere/testimage01_color.tar.gz`

The url `http://www.example.com/testimage45.png` will be ignored.

# Image Examples

See the files in the [examples](./examples) folder.
