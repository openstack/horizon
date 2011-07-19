from django import http


def fakeView(request):
    resp = http.HttpResponse()
    resp.write('<html><body><p>'
               'This is a fake httpresponse from a fake view for testing '
               ' purposes only'
               '</p></body></html>')

    return resp
