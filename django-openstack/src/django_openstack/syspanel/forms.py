from django import forms


class DisableProject(forms.Form):
    project_name = forms.CharField()


class DisableIpAddress(forms.Form):
    cidr = forms.CharField()
