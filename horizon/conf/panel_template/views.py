from horizon import views


class IndexView(views.APIView):
    # A very simple class-based view...
    template_name = '{{ dash_name }}/{{ panel_name }}/index.html'

    def get_data(self, request, context, *args, **kwargs):
        # Add data to the context here...
        return context
