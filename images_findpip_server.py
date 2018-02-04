##########
#
# Python 3.6 version of the script
#
# Created: 2018-01-02
# Modified: 2018-01-18 1757
##########

# Python built-in modules
import sys
import math
import numpy as np
import os
import re
import select
import shutil
import socket
import tarfile
import tempfile
import urllib.request
import urllib.error

import cv2

class ServerObject:

    def __init__(self):

        # Server version
        self.serverversion = '0.24.3'

        # Enable/Disable debug mode
        # True = Write debug info to the console and possibly to debug.txt
        # False = Nothing will be written to the console. The debug.txt file
        #         will not be created
        self.debugmode = True

        # Enable/Disable writing to debug.txt
        # True = Write debug info to debug.txt and include it in the .tar.gz file
        # False = Do not create the debug.txt file.
        self.debugfile = False

        # Should the output images be in color or grayscale?
        # Note: If the source image is alread in grayscale, this setting
        #       will have no effect on the output images.
        #
        # Note: I might expose this option later so leave it here.
        self.returncolor = False

        # Initialize an empty list
        self.debuglog = []

        # Where should the server put its ear?
        self.port = 6003

        if self.debugmode:
            # IP address and port number
            self._writeToDebugFile("images_findpip Server v{}".format(self.serverversion), '')
            self._writeToDebugFile("Initializing server...", '')
            self._writeToDebugFile("Host: {}".format(socket.gethostname()), '')
            self._writeToDebugFile("Port: {}".format(self.port), '')

        # Create a listening socket
        self.srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srvsock.bind(("", self.port)) #Listens on all IP addresses
        self.srvsock.listen(5) # This is what makes it a listening socket. Allow upto 5 queued connections.

        # Keep track of the connections
        # Using a list makes it easy to add/remove client connection info
        self.socklist = [self.srvsock]

        self._endmarker = '~~~'

        if self.debugmode:
            self._writeToDebugFile("Server ready.", '')

    def _acceptNewConnection(self):

        if self.debugmode:
            self._writeToDebugFile("Entered _acceptNewConnection()", '')

        newsock, (remhost, remport) = self.srvsock.accept()

        if self.debugmode:
            self._writeToDebugFile("Connection accepted from {}:{}".format(remhost, remport), '')

        self.socklist.append(newsock)

    def _cleanUp(self, clientdata, filename):

        # Remove the temp directory
        if os.path.exists(clientdata[1]):
            shutil.rmtree(clientdata[1])

        # Remove the .tar.gz file or _specialURL() file
        if os.path.isfile(filename):
            os.unlink(filename)

    def _createGzipFile(self, clientdata):
        # Creates a .tar.zip file containing the contents of <clientdata[1]>

        # Change into the directory that contains the files
        # to be sent back to the caller.
        os.chdir(clientdata[1])

        # Create the .tar.gz file with the results
        filename = os.path.join(tempfile.gettempdir(), clientdata[2]) + '.tar.gz'

        # Delete the source image since they already have access to it elsewhere
        #
        # Need to check if file exists incase an error occured before the file
        # could be created on the server.
        if os.path.isfile(clientdata[3]):
            os.unlink(clientdata[3])

        if self.debugmode:
            self._writeToDebugFile(".tar.gz file - {}".format(filename), clientdata)

        with tarfile.open(filename, 'w:gz') as f:
            f.add('.')
        f.close()

        return filename

    def _extCheck(self, fname, clientdata):
        # Restrict files to image files

        if self.debugmode:
            self._writeToDebugFile("Entered _extCheck()", clientdata)

        # List of valid file extensions
        choices = ('jpg', 'jpeg', 'jpe', 'jp2', 'png', 'bmp', 'dib', 'webp', 'pbm', 'pgm', 'ppm', 'sr', 'ras', 'tiff', 'tif')

        # Get file extension
        ext = os.path.splitext(fname)[1][1:]

        # Check if extension is valid
        if ext not in choices:
            # File Rejected

            self._writeToErrorFile("File does not end with one of {}".format(choices), clientdata)
            self._send(clientdata)

            return False, False

        return fname.split(".")

    def _parseData(self, data):

        if self.debugmode:
            self._writeToDebugFile("Entered _parseData()", '')

        # Find the first url in <data>
        rv = re.search(r'(ftp|http|https)://.*?\.(jpg|jpeg|jpe|jp2|png|bmp|dib|webp|pbm|pgm|ppm|sr|ras|tiff|tif)', data)
        url = rv.group(0)

        # Remove the url
        data = data.replace(url, '')

        # Split <data> into an array in preperation for searching for options
        values = data.split("***")

        # Search for the options
        for v in values:

            # Convert to lower case for easier matching
            v = v.lower()

            if v == 'debugmodeoff':
                self.debugmode = False

            if v == 'debugfileon':
                self.debugfile = True

            if v == 'returncolor':
                self.returncolor = True

        if self.debugmode:
            self._writeToDebugFile("Parsed URL: {}".format(url), '')

        return url

    def _processImage(self, url, clientdata):
        #
        # This function does most of the work of processing the image
        #

        if self.debugmode:
            self._writeToDebugFile("Entered _processImage()", clientdata)

        # Get file name from URL
        fname = url.split('/')[-1:][0]

        # Full path to source image
        srcimage = clientdata[1] + '/srcimage_' + fname

        clientdata.append(srcimage)

        fname, ext = self._extCheck(fname, clientdata)

        if not ext:
            # Invalid extension
            return False

        if self.debugmode:
            self._writeToDebugFile("Returned to _processImage()", clientdata)

        req = urllib.request.Request(url)

        try:
            # Download the image to memory
            image = urllib.request.urlopen(req)

        except urllib.error.HTTPError as e:
            msg = "The server couldn\'t fulfill the request.\nError code: {}".format(e.code)

            if e.code == 404:
                msg += " (File not found)"

            msg += "\n\nURL received: {}".format(url)

            self._writeToErrorFile(msg, clientdata)
            return self._send(clientdata)

        except urllib.error.URLError as e:
            self._writeToErrorFile("Failed to reach the server.\nReason: {}\n\nURL received: {}".format(e.reason, url), clientdata)
            return self._send(clientdata)

        # Save image to disk
        with open(srcimage, "wb") as local_file:
            local_file.write(image.read())
        local_file.close()

        # Load in the source image
        imgorig = cv2.imread(srcimage)

        # Check for corrupt image
        if imgorig is None:
            self._writeToErrorFile("Image file appears to be corrupted.\n\nURL received: {}".format(url), clientdata)
            return self._send(clientdata)

        if self.debugmode:
            self._writeToDebugFile("Image loaded.", clientdata)

        # Calculate dimensions for resized image
        ratio = 500.0 / imgorig.shape[1]
        dim = (500, int(imgorig.shape[0] * ratio))

        # Resizing of image is done here to speed up processing
        try:
            img = cv2.resize(imgorig, dim, interpolation = cv2.INTER_AREA)
        except Exception as e:
            msg = "Unable to resize image.\n"

            for a in e:
                msg += "\n" + str(a)

            msg += "\n\nURL received: {}".format(url)

            if self.debugmode:
                self._writeToDebugFile(msg + "\nOriginal dimensions: {}x{}\nNew dimensions: {}x{}".format(imgorig.shape[0], imgorig.shape[1], dim[0], dim[1]), clientdata)

            self._writeToErrorFile(msg, clientdata)
            return self._send(clientdata)

        if self.debugmode:
            self._writeToDebugFile("Image copied and resized.", clientdata)

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        if self.debugmode:
            # Save the grayscale version to disk so it will be included
            grayfilename = clientdata[1] + "/"+ fname + "_grayscale." + ext
            try:
                cv2.imwrite(grayfilename, gray)
            except Exception as e:
                # The grayscale image needs to be written to disk
                # so that the computer does not run out of memory.

                msg = "Unable to save grayscale image.\nDestination file: {}".format(grayfilename)

                for a in e:
                    msg += "\n"+str(a)

                self._writeToDebugFile(msg, clientdata)

                return self._send(clientdata)
            else:
                self._writeToDebugFile("Grayscale image created", clientdata)

        # Add a blur to remove some of the noise
        # Image noise is random variation of brightness or color.
        # More info: https://en.wikipedia.org/wiki/Image_noise
        gray = cv2.GaussianBlur(gray, (11,11), 0)

        # Find the contours of the receipe cards
        edge = cv2.Canny(gray, 100, 200)
        _, contours, _ = cv2.findContours(edge.copy(), 1, 1)

        if len(contours) < 1:
            # Unable to pull anything out of the image if no contours were found
            self._writeToErrorFile("No contours found to retreive\n\nURL received: {}".format(url), clientdata)
            return self._send(clientdata)

        if self.debugmode:
            self._writeToDebugFile("Number of contours: {}".format(len(contours)), clientdata)

        # Give each output image a unique name
        loopcnt = -1

        # Keep track of track of the number of conturs saved to disk
        numsaved = 0

        # Process all found contours
        for pos in contours:

            loopcnt+=1

            if self.debugmode:
                self._writeToDebugFile("Loop: {}".format(loopcnt), clientdata)

            # Each receipe card has two contours. Don't know why.
            #
            # The first contour is an exact copy of the card in the original image.
            # The second contour is rotated slightly and has a small border that makes
            #     it easier for the OCR script to find the text near the edge of the image.
            #
            # This if..then skips the first contour.
            if loopcnt % 2 == 0: continue

            # Get length of the contour in pixels
            # <peri> is a float
            peri = cv2.arcLength(pos, True)

            # Approximates a polygonal curve(s) with the specified precision
            # More info: https://docs.opencv.org/2.4/modules/imgproc/doc/structural_analysis_and_shape_descriptors.html#approxpolydp
            approx = cv2.approxPolyDP(pos, 0.02 * peri, True)

            # Find the corners and dimensions of the object
            w, h, arr = self._transform(approx, clientdata)

            if self.debugmode:
                self._writeToDebugFile("Returned to _processImage()", clientdata)

            if w == -1 and h == -1 and arr == -1:
                # An error ocurred in _transform()
                return self._send(clientdata)

            # Only process contours that have a valid dimension
            if w > 0 and h > 0:

                # Adjust width and height to match dimensions of
                # each receipe card on the original image
                wr = int(w / ratio)
                hr = int(h / ratio)

                # Adjust pixel coordinates to match orignal image
                arr_us=[]
                for a in arr:
                    a[0] = int(math.floor(a[0] / ratio))
                    a[1] = int(math.floor(a[1] / ratio))
                    arr_us.append(list(a))

                arr = arr_us

                # Convert all of the numbers to floats
                pts1 = np.float32(arr)
                pts2 = np.float32([[0, 0], [wr, 0], [0, hr], [wr, hr]])

                # Changes perspective to a top-down view (a.k.a.: birds eye view)
                M = cv2.getPerspectiveTransform(pts1, pts2)
                dst = cv2.warpPerspective(imgorig, M, (wr, hr))

                if self.returncolor:
                    # Keep original image colors in output images
                    image = dst
                else:
                    # Convert output images to grayscale before saving
                    image = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY)

                # Save each receipe card to individual image files
                outfilename = clientdata[1] + "/"+ fname + "_result_" + str(loopcnt) + "." + ext

                try:
                    # WARNING: This will overwrite existing files.
                    cv2.imwrite(outfilename, image)

                except Exception as e:
                    msg = "Unable to save extracted image to disk."

                    for a in e:
                        msg += "\n"+str(a)

                    if self.debugmode:
                        self._writeToDebugFile(msg + "\nDestination file: {}".format(outfilename), clientdata)

                    self._writeToErrorFile(msg, clientdata)
                    return self._send(clientdata)

                numsaved += 1
            else:
                if self.debugmode:
                    self._writeToDebugFile("\nContur width and/or height are to small to process.", clientdata)

        if numsaved < 1:
            self._writeToErrorFile("Did not find anything to extract from source image.\n\nURL received: {}".format(url), clientdata)

        # Free up some of the Raspberry Pi's memory
        imgorig = None

        # Finished processing.
        # Send the results.
        return self._send(clientdata)

    def _receive(self, sock):
        total_data=[];
        data=''

        if self.debugmode:
            self._writeToDebugFile("Entered _receive()", '')

        while True:

            # Get data from client
            data = sock.recv(1024)

            # Convert to string
            data = str(data, encoding='utf-8')

            if self._endmarker in data:
                # Received entire message.

                # Removes self._endmarker from the data
                total_data.append(data[:data.find(self._endmarker)])
                break
            else:
                # Only got part of the message
                total_data.append(data)

            if len(total_data) > 1:
                #check if self._endmarker got split during transmission
                last_pair = total_data[-2] + total_data[-1]

                if self._endmarker in last_pair:
                    total_data[-2] = last_pair[:last_pair.find(self._endmarker)]
                    total_data.pop()
                    break


        # Put all of the received data into one long string
        data = ''.join(total_data)

        url = self._parseData(data)

        if self.debugmode:
            self._writeToDebugFile("Returned to _receive()", '')

        return url

    def _send(self, clientdata):
        # Create and then send the .tar.gz file

        if self.debugmode:
            self._writeToDebugFile("Entered _send()", clientdata)

        filename = self._createGzipFile(clientdata)

        if self.debugmode:
            self._writeToDebugFile("Returned to _send()", clientdata)

        f = open(filename,'rb')
        while True:

            l = f.read(1024)

            while (l):
                try:
                    clientdata[0].send(l)
                except socket.error:
                    # Connection unexpectedly terminated
                    # Clean up
                    self._cleanUp(clientdata, filename)
                    return False

                l = f.read(1024)

            if not l:
                f.close()
                break

        if self.debugmode:
            # Note: This line will never be seen in debug.txt because it
            #       is printed after the file has been sent to the client.
            print("Debug: Sent file")

        self._cleanUp(clientdata, filename)

        if self.debugmode:
            # Note: This line will never be seen in debug.txt because it
            #       is printed after the file has been deleted.
            print("Debug: Deleted data")

        return True

    def _sendSpecial(self, clientdata, filename):
        # Create and then send the .tar.gz file

        if self.debugmode:
            self._writeToDebugFile("Entered _sendSpecial()", clientdata)

        f = open(filename,'rb')
        while True:

            l = f.read(1024)

            while (l):
                try:
                    clientdata[0].send(l)
                except socket.error:
                    # Connection unexpectedly terminated
                    # Clean up
                    self._cleanUp(clientdata, filename)
                    return False

                l = f.read(1024)

            if not l:
                f.close()
                break

        if self.debugmode:
            # Note: This line will never be seen in debug.txt because it
            #       is printed after the file has been sent to the client.
            print("Debug: Sent file")

        self._cleanUp(clientdata, filename)

        if self.debugmode:
            # Note: This line will never be seen in debug.txt because it
            #       is printed after the file has been deleted.
            print("Debug: Deleted data")

        return True

    def _specialURLs(self, url, clientdata):
        # Special URLs allow the client to retrieve a help/description file and
        # the scripts version number

        # The URLs and their meanings
        #
        # http://helpme
        #   Sends a text file containing instructions on how to use this script and
        #   the scripts version number.
        #
        # http://version
        #   Sends a text file containing only the scripts version number

        url = url.lower()

        if url == 'http://helpme':
            filename = clientdata[1]+'/help.txt'
            with open(filename, 'w') as f:
                f.write("images_findpip Server v{}\n\n".format(self.serverversion))
                f.write("IP Address: {}\n".format(socket.gethostname()))
                f.write("Port: {}".format(self.port))
                f.write("\n\nDescription:\n")
                f.write("    Given an image, tries to find all of the pictures within that image.")
                f.write("\n\nUsage:\n")
                f.write("    curl -d \"<image_url>\" http://<openfaas_ip>:8080/function/images_findpip > ~/results.tar.gz")
                f.write("\n\nReturns:\n")
                f.write("    The returned data is a gz file (.tar.gz). To save the data, you will need to use a redirect (>).")
                f.write("\n    Without the redirect, your screen will fill up with random characters.")
                f.write("\n    If this happens, press Ctrl-C and resend the URL to the script with a redirect added as shown in the Usage section")
                f.write("\n\nBackground Color:")
                f.write("\n    The sharper the contrast between the background color and the picture(s) you want pulled out, the easier it will")
                f.write("\n    be for the script to find the edges of the picture(s).")
                f.write("\n\n    If the picture(s) you want extracted have a mostly white background, try a solid brown, green, or black.")
                f.write("\n\nSpecial URLs:")
                f.write("\n    There are some special URLs that can be sent to this script. You do not need to use a redirect (>) with these URLs")
                f.write("\n    because they return text. You must include the http:// part or the script will try to process your request as an image.")
                f.write("\n\n    http://helpme")
                f.write("\n        Generates the help file you are currently reading. Includes script version number.")
                f.write("\n\n    http://version")
                f.write("\n        Sends a text file containing only the scripts version number.")
                f.write("\n\nWhy I wrote this script:")
                f.write("\n    My mom has alot of receipes hand written on 3\"x5\" index cards. She also has alot of receipes cut out of magazines")
                f.write("\n    and newspapers glued onto index cards. With most of these cards over 10 years old, the hand writing is starting to")
                f.write("\n    fade and the glue is losing its stickyness.")
                f.write("\n\n    The receipe drawer has 3 shoe boxes filled with receipes and no one wants to rewrite that many receipes. She also has")
                f.write("\n    some receipe books in there that have to be kept in a bag so none of the pages get lost.")
                f.write("\n\n    So to save these receipes, I decided create a website and database to view and edit them along with a number of scripts")
                f.write("\n    to partially automate the process of entering the receipes into the websites database.")
                f.write("\n\nHow I create the source images for this script:")
                f.write("\n    1) Place receipes on scanner glass")
                f.write("\n    2) Lay large solid color paper on top of receipe cards")
                f.write("\n        I use a piece of flat black construction paper that is larger than the scanner glass.")
                f.write("\n    3) Close scanner lid and scan to color image")
                f.write("\n        Since the script converts the source image to grayscale<https://en.wikipedia.org/wiki/Grayscale> (a.k.a black and white)")
                f.write("\n        before searching for the receipe cards, you do not need to use a color scanner.")
                f.write("\n\n        I scan to color because some of the receipes include a picture of the finished item that I want to add to the website.")
                f.write("\n    4) Send image from scanner to images_findpip<link> for seperation")
                f.write("\n    5) Send the images from step 4 to images_ocr<link> for OCR<link> processing")
                f.write("\n        This OCR script does three things:")
                f.write("\n            - Finds receipe name")
                f.write("\n            - Finds the ingredients list and places each ingredient on one line")
                f.write("\n            - Finds the directions and \"unwraps\" each paragraph so each paragraph is on one line")
                f.write("\n    6) Check OCR results for missing/wrong/mangled text, and update scripts")
                f.write("\n        6a) Restart at step 5 if scripts are modified")
                f.write("\n        6b) Manually edit text that is not fixed by updating the scripts")
                f.write("\n    7) OCR results uploaded to cook book database")
                f.write("\n        Currently this is done manually via lots of copy and paste motions but I do plan to automate as")
                f.write("\n        much of this step as possible after getting the OCR scripts outputting acceptable results.")
                f.write("\n")
            f.close()

            self._sendSpecial(clientdata, filename)

            # URL is a special URL    
            return True

        elif url == 'http://version':
            filename = clientdata[1]+'/version.txt'
            with open(filename, 'w') as f:
                f.write("{}\n".format(self.serverversion))
            f.close()

            self._sendSpecial(clientdata, filename)

            # URL is a special URL    
            return True

        # URL is not a special URL
        return False

    def _transform(self, pos, clientdata):
        # This function is used to find the corners and dimensions of the object

        if self.debugmode:
            self._writeToDebugFile("Entered _transform()", clientdata)

        pts=[]
        n=len(pos)

        for i in range(n):
            pts.append(list(pos[i][0]))

        sums={}
        diffs={}
        tl=tr=bl=br=0

        for i in pts:
            x=i[0]
            y=i[1]
            sum=x+y
            diff=y-x
            sums[sum]=i
            diffs[diff]=i

        sums=sorted(sums.items())
        diffs=sorted(diffs.items())
        n=len(sums)

        try:
            rect=[sums[0][1],diffs[0][1],diffs[n-1][1],sums[n-1][1]]
            #       top-left   top-right   bottom-left   bottom-right
        except IndexError as e:
            msg = ''
            for a in e:
                msg += str(a) + "\n"

            self._writeToErrorFile(msg, clientdata)
            return int(-1), int(-1), int(-1)

        h1 = np.sqrt((rect[0][0]-rect[2][0])**2 + (rect[0][1]-rect[2][1])**2)        #height of left side
        h2 = np.sqrt((rect[1][0]-rect[3][0])**2 + (rect[1][1]-rect[3][1])**2)        #height of right side
        h = max(h1, h2)

        w1 = np.sqrt((rect[0][0]-rect[1][0])**2 + (rect[0][1]-rect[1][1])**2)        #width of upper side
        w2 = np.sqrt((rect[2][0]-rect[3][0])**2 + (rect[2][1]-rect[3][1])**2)        #width of lower side
        w = max(w1, w2)

        return int(w), int(h), rect

    def _writeToDebugFile(self, text, clientdata):

        if clientdata == '':
            # Store in a list until we know what file to write it to
            self.debuglog.append(text)

        else:

            if self.debugfile:
                # Write debug messages to debug.txt
                # This file will only be created if debugfile == True

                with open(clientdata[1]+'/debug.txt', 'a') as f:

                    if debugmode and len(self.debuglog) > 0:
                        # Save debug logs generated this file was available for writing
                        for d in self.debuglog:
                            f.write(str(d)+"\n")

                        # Clear the log so it does not get written to
                        # the file multiple times
                        self.debuglog = []

                    f.write(str(text)+"\n")
                f.close()

        # Always display message on screen
        print("Debug: {}".format(text))

    def _writeToErrorFile(self, text, clientdata):
        # Write error message to error.txt

        print("Debug: Entered _writeToErrorFile()")

        with open(clientdata[1]+'/error.txt', 'a') as f:
            f.write(str(text)+"\n")
        f.close()

        # Always display message on screen
        print("Error: {}".format(text))

    def close(self):
        # Close connections and stop server

        for sock in self.socklist:
            sock.close

    def run(self):
        #
        # Main entry point into server
        #

        if self.debugmode:
            self._writeToDebugFile("Entered run()", '')

        #####
        # Begin main loop
        while True:

            if self.debugmode:
                # Helps to visually seperate the code path for each client
                # Do not put into the debug.txt file that gets sent to each client
                print("\n==========\n")

                self._writeToDebugFile("select.select() waiting...", '')

            # Await an event on a readable socket descriptor
            (sread, swrite, sexc) = select.select(self.socklist, [], [])

            # Iterate through the tagged read socklist
            for sock in sread:

                # Received a connect to the server (listening) socket
                if sock == self.srvsock:
                    self._acceptNewConnection()

                    if self.debugmode:
                        self._writeToDebugFile("Returned to run()", '')

                    # Goto top of main loop
                else:

                    # Received something on a client socket
                    rv = self._receive(sock)

                    if self.debugmode:
                        self._writeToDebugFile("Returned to run()", '')

                    if rv != False:

                        # Check to see if the peer socket closed
                        if rv == '':
                            # Client disconnected
                            sock.close
                            self.socklist.remove(sock)
                        else:
                            # Received some data so try to process it as an image

                            tempdir = tempfile.mkdtemp()
                            clientdata = [sock, tempdir, list(os.path.split(tempdir))[-1:][0]]
                                                         # .tar.gz file name - Note the nested list calls

                            if not self._specialURLs(rv, clientdata):
                                # No special URL received so process the data as an image
                                self._processImage(rv, clientdata)

                            # Close the connection
                            try:
                                sock.shutdown(socket.SHUT_RDWR)
                            except socket.error as e:
                                print("Debug: Connection closed unexpectedly")
                                print("Reason: {}".format(e))
                            else:
                                sock.close
                                print("Debug: Closed connection")

                            # Always remove the client info
                            self.socklist.remove(sock)

                    else:
                        if self.debugmode:
                            self._writeToDebugFile("rv equals false", clientdata)
                        else:
                            pass


if __name__ == '__main__':

    try:
        # Start the server
        talk = ServerObject()
        talk.run()
    
    except KeyboardInterrupt as e:
        # Shutdown the server
        talk.close()

##########
# Change Log:
#
# 0.24.3 (2018-01-20):
#       Added function _parseData()
