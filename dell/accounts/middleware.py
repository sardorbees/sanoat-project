from django.shortcuts import redirect

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:
            if request.user.must_change_password and request.path != "/change-password/":
                return redirect("/change-password/")

        return self.get_response(request)
