import smtplib


def send_email(from_email, to_email, message, subject = 'No Subject'):
    # create smtp object
    smtpObj = smtplib.SMTP('smtp.gmail.com', 587)

    # Say hello!
    smtpObj.ehlo()

    # start TLS Encryption
    smtpObj.starttls()

    sender = 'marcusdambrosio@gmail.com'
    sender_password = 'qulqqxystaqmkddz'
    smtpObj.login(sender, sender_password)

    if subject:
        send = smtpObj.sendmail(from_email, to_email, f'Subject: {subject}\n{message}')


    else:
        send = smtpObj.sendmail(from_email, to_email, message +'\n\nThis is an automated email.')

    if not send:


        print('EMAIL SENT')
    smtpObj.quit()


