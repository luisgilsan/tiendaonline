from django.shortcuts import render, reverse
from django.views import generic
from .forms import ContactForm
from django.core.mail import send_mail
from store import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from cart.models import Order

class ProfileView(LoginRequiredMixin,generic.TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        orders = Order.objects.filter(user_id=self.request.user)
        context.update({
            'orders' : Order.objects.filter(user=self.request.user, ordered=True),
            'all_orders' : orders
        })
        return context

class HomeView(generic.TemplateView):
    template_name = 'index.html'

class ContactView(generic.FormView):
    form_class = ContactForm
    template_name = 'contact.html'

    def get_success_url(self):
        return reverse("contact")

    def form_valid(self, form):
        messages.info(self.request,
            'Hemos recibido tu mensaje!')
        name = form.cleaned_data.get('name')
        email = form.cleaned_data.get('email')
        message = form.cleaned_data.get('message')
        full_message = f"""
            Mensaje recibido de {name}, {email} 
            __________________________

            {message}

        """
        send_mail(subject="Petición de Cliente",
            message=full_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.NOTIFY_EMAIL]
            )
        return super(ContactView,self).form_valid(form)

