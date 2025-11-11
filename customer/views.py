from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Customer, Address
from .forms import CustomerForm, AddressFormSet


class CustomerListView(LoginRequiredMixin, ListView):
    """
    View para listagem de clientes com busca e paginação.
    """
    model = Customer
    template_name = 'customer/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(cpf_cnpj__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class CustomerDetailView(LoginRequiredMixin, DetailView):
    """
    View para exibir detalhes do cliente e histórico.
    """
    model = Customer
    template_name = 'customer/customer_detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.get_object()
        
        # Adiciona informações de histórico (placeholder)
        context['purchase_history'] = customer.get_purchase_history()
        context['total_spent'] = customer.get_total_spent()
        context['purchase_frequency'] = customer.get_purchase_frequency()
        context['favorite_products'] = customer.get_favorite_products()
        
        # Adiciona endereços
        context['addresses'] = customer.addresses.all()
        
        return context


class CustomerCreateView(LoginRequiredMixin, CreateView):
    """
    View para criar novo cliente com endereços.
    """
    model = Customer
    form_class = CustomerForm
    template_name = 'customer/customer_form.html'
    success_url = reverse_lazy('customer:customer_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['address_formset'] = AddressFormSet(self.request.POST)
        else:
            context['address_formset'] = AddressFormSet()
        context['action'] = 'Cadastrar'
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        address_formset = context['address_formset']
        
        if address_formset.is_valid():
            self.object = form.save()
            address_formset.instance = self.object
            address_formset.save()
            messages.success(self.request, f'Cliente "{self.object.name}" cadastrado com sucesso!')
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    """
    View para editar cliente existente.
    """
    model = Customer
    form_class = CustomerForm
    template_name = 'customer/customer_form.html'
    success_url = reverse_lazy('customer:customer_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['address_formset'] = AddressFormSet(self.request.POST, instance=self.object)
        else:
            context['address_formset'] = AddressFormSet(instance=self.object)
        context['action'] = 'Editar'
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        address_formset = context['address_formset']
        
        if address_formset.is_valid():
            self.object = form.save()
            address_formset.instance = self.object
            address_formset.save()
            messages.success(self.request, f'Cliente "{self.object.name}" atualizado com sucesso!')
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)


class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    """
    View para deletar cliente.
    """
    model = Customer
    template_name = 'customer/customer_confirm_delete.html'
    success_url = reverse_lazy('customer:customer_list')
    context_object_name = 'customer'

    def delete(self, request, *args, **kwargs):
        customer = self.get_object()
        messages.success(request, f'Cliente "{customer.name}" removido com sucesso!')
        return super().delete(request, *args, **kwargs)
