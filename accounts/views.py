from django.db.models.query_utils import Q
from django.shortcuts import render, get_object_or_404,redirect
import random

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib import messages
from django.views import View

from . import serializers
from .models import Account,SocialLogin,UserOtp

#For authentication
from django.contrib.auth import authenticate,logout,login

#For email verification

from django.core.mail import send_mail


def create_otp(email):
    otp = random.randint(10000, 99999)

    if UserOtp.objects.filter(email=email).exists():
        UserOtp.objects.get(email=email).delete()

    user_otp = UserOtp(email=email, code=otp)
    user_otp.save()
    return user_otp.code


def verify_otp(email, otp):
    if UserOtp.objects.filter(email=email).exists():
        user_otp = UserOtp.objects.get(email=email)
        if str(otp) == str(user_otp.code):
            user_otp.delete()
            return True
        else:
            return False
    else:
        return False

#The send email function
def send_email(request, account, mail_subject,message): 
    send_mail(
        mail_subject,
        message,
        'noreply@bauss.com',
        [account.email],
        fail_silently=False,
    )
    

class check_user(View):
    def get(self,request,user):
        data ={}
        try:
            if Account.objects.filter(email=user).exists() == True:
                account = Account.objects.get(email=user)
                result = True
                data["fullname"]     = account.fullname
                data['profile_image']  = str(account.profile_image.url)
            else:
                result = False
            data["result"]     = result
        except:
            data["Error"]     = "Sorry something when wrong"
        template_name = 'report.html'
        return render(request, template_name,data)
# Create your views here.
class user_view(View):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data = {}
        user =  get_object_or_404(Account, email=request.user.email)
        serializer = serializers.AccountSerializer(user)
        data = serializer.data
        data['email_verified'] = user.email_verified
        data['profile_image'] = data['profile_image']
        template_name = 'report.html'
        return render(request, template_name, data, status=status.HTTP_200_OK)

     #for Updating user 
    def put(self, request):
        data = {}
        user =  get_object_or_404(Account, email=request.user.email)

        serializer = serializers.AccountSerializer(user, data=request.data)

        if serializer.is_valid():
            serializer.save()
            data = serializer.data
            data['email_verified'] = user.email_verified
            # if user.plan != None:
            #     data['plan'] = user.plan.space_size
            #     data['plan_desc'] = user.plan.desc
            #     data['amount'] = user.plan.amount
            # else:
            #     data['plan'] = None
            #     data['plan_desc'] = None
            #     data['amount'] = None
            data['profile_image'] = data['profile_image']
            data['success'] = "Success"

        else:
            data = serializer.errors   
        
        template_name = 'report.html'
        return render(request, template_name,data,  status=status.HTTP_200_OK)

#Register users
class forgotpassword(View):

    def get(self, request):
        template_name = 'forgotpassword.html'
        return render(request, template_name)

    def post(self, request):
        data = {}   #This is all the data that is been passed to the api Eg. Contex variables
        # current_site = get_current_site(request)
        email = request.POST['email']
        otp = create_otp(email)
        data['otp'] = otp

        template_name = 'verifyaccount.html'
        return render(request, template_name,data)

#Login view for validation
class login_view(View):
    data = {}  

    def get(self, request):
        template_name = 'home.html'
        return render(request, template_name)
    
    def post(self, request):
        credentials = request.POST['username']
        password = request.POST['password']
        # Check if username or email exist 
        if Account.objects.filter(email=credentials).exists()==True:
            account_cred =  Account.objects.get(email=credentials) 	

        elif Account.objects.filter(username=credentials).exists()==True:
            account_cred =  Account.objects.get(username=credentials) 	

        else:
            account_cred = None
            self.data['error'] = "Username/Email not found"

        # If it does, it means the password doesnt match 
        if account_cred:
            # Check if username and passowrd match
            userAuth = authenticate(username=account_cred, password=password) 

            if userAuth is not None:	
                login(request,userAuth)				 		
                self.data['error'] = False
            else:
                self.data['error'] = "Incorrect password"

        return redirect("/main/get/offense")

#Login view for validation
class verify_email(View):
    data = {}  
    def post(self, request):
        # email = request.POST['email']
        # otp = request.POST['otp']
        # result = verify_otp(email,otp)
        # if result == True:
        #     request.user.email_verified = True
        #     request.user.save()
        #     self.data['success'] = "Successfully Verified email"
        # else:
        #     self.data['error'] = "OTP code is invalid"
        return redirect("/main/get/offense")

# Login with google 


def welcome_email_view(request):
    data = {}
    account =  get_object_or_404(Account, email=request.data['email'])
    if account.email_verified is not True:
        message = f"Hi,{account.fullname} you are welcome, ENJOY "
        send_email(request, account,"Welcome to BAUSS",message)
    else:
        data['verified'] = True
    data['success'] = "Success"
    template_name = 'report.html'
    return render(request, template_name,data, status=status.HTTP_200_OK)



def setting_password(request):
    password = request.POST['password']
    confirm_password = request.POST['confirm_password']

    if password == confirm_password:
        user = request.user
        user.set_password(password)
        user.save()
        data ={}
        data['success'] = "Successfully set password"
        messages.success(request, "data")
        template_name = 'report.html'
        return render(request, template_name,data, status=status.HTTP_200_OK)
    else:
        messages.success(request, "data")
        template_name = 'report.html'
        return render(request, template_name,data, status=status.HTTP_200_OK)
