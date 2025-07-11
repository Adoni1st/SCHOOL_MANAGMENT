School managment system

Table of Contents
    1.Setup
    2.Features
        - Schedule Management
        - Discussion
        - Attendance
        - Announcements
        - Users, Classes, and Subjects

Setup
- to install all the required dependencies run the following command on your terminal

    pip install -r requirements.txt

- to start the program you run only main.py for a single device which should take you to a sign in/sign up page. enter all the required information and click sign up if you are new or sign in if you had an existing account.

the program contains the following main features.

schedule managment: it consists a user friendly UI which gives the user the option to create a schedule manually or generate a schedule based on the inputs given. after that these schedule can be saved and edited by the user. this feature exists for admins only.

Discussion: it is a feature where students and teachers can freely communicate via messages on a LAN server. at first the teacher needs to start a server on a LAN, after that any student can join the chat as a client as long as they are connected to the same LAN

Attendance: it is a feature that let the teacher mark attendance in a very easy and efficient way without a need for a face recognition system. the attendance works as follows:
- the teacher opens the attencdance tab and starts a server where his/her server's ip will be displayed in a screen which is visible to all students
- students join as a client to the server where they will have a different UI, the students enter the teacher's ip and connect to the server. they will enter their class id to identify themselves
- after that the teacher's screen will be displaying a TOTP code that changes every twenty seconds.
- students not only have to enter that TOTP code within 20 seconds befoe it changes, but also have to verify their identity via an email verification code. this ensures the user that is marking attendance is the user that logged in.
-after these steps the user clicks mark attendance and if all the criterias are met, attendance wil be marked and saved with the day they attended and the time.
this feature exists in student and teachers' dashboard(UI) only

Announcments: is a feature where the admin can announce news to all users displaying the date and the importance of the announcment. this makes it more accessible for students and teachers to get the important news without mixing it with normal chats like what happens in telegram.

users, classes and subjects: these are features that exist within the admin's dashboard(UI) and it makes it very easy and efficient to add or remove new users wether they are studentss or teachers, add or remove subjects, add these subjects in the classes along with the teachers that teach the specific subject

- those were the main features but the program also includes other minor features that would be covered in the presentation. 

- this project uses modern GUI with customtkinter and tkinter.