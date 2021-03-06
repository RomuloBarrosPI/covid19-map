from django.shortcuts import redirect
from django.views.generic import TemplateView
from .models import CasosPorCidadePiaui
from datetime import date
import json
import requests
import contextlib


def soma_obitos_brasil(data_brasil):
    soma = 0 
    for state in data_brasil:
        soma += int(state['deaths'])
    return soma


def soma_casos_brasil(data_brasil):
    soma = 0 
    for state in data_brasil:
        soma += int(state['confirmed'])
    return soma
    

def deaths_for_state(data_new_confirmed):
    data_parsed = []
    for state in data_new_confirmed:
        parsed = state['state'], int(state['last_available_deaths'])
        data_parsed.append(parsed)
    return sorted(data_parsed, key=lambda tup: tup[1], reverse=True)


def new_cases_for_state(data_new_confirmed):
    data_parsed = []
    for state in data_new_confirmed:
        parsed = state['state'], int(state['new_confirmed'])
        data_parsed.append(parsed)
    return sorted(data_parsed, key=lambda tup: tup[1], reverse=True)


def new_deaths_for_state(data_new_confirmed):
    data_parsed = []
    for state in data_new_confirmed:
        parsed = state['state'], int(state['new_deaths'])
        data_parsed.append(parsed)
    return sorted(data_parsed, key=lambda tup: tup[1], reverse=True)


def get_casos_por_estado(data):
    data_parsed = []
    for state in data:
        parsed = 'br-' + state['state'].lower(), int(state['confirmed'])
        data_parsed.append(parsed)
    return data_parsed 


def get_request_ultimos_dados(url):
    response = requests.get(url)
    response = json.loads(response.text)
    data = response['results']
    return data
        

def get_request_data_new_cases_for_state(url):
    response = requests.get(url)
    response = json.loads(response.text)
    data = response['results']
    return data


def get_request_data_new_cases(url):
    response = requests.get(url)
    response = json.loads(response.text)

    data_parsed = []
    for data in response:
        parsed = date(date.today().year, int(data['label'][4::]), int(data['label'][:2:])), data['data']
        data_parsed.append(parsed)
    return data_parsed


def get_request_data(url):
    response = requests.get(url)
    response = json.loads(response.text)

    data_parsed = []
    for data in response:
        parsed = date(int(data['data'][:4:]), int(data['data'][5:7:]), int(data['data'][8:10:])), data['quantidade']
        data_parsed.append(parsed)
    return data_parsed


def casos_confirmados():
    url = 'http://coronavirus.pi.gov.br/public/api/casos/confirmados.json'
    return get_request_data(url)


def historico_mortes():
    url = 'http://coronavirus.pi.gov.br/public/api/casos/obitos.json'
    return get_request_data(url)


def novos_casos():
    url = 'http://coronavirus.pi.gov.br/public/api/novos-casos.json'
    return get_request_data_new_cases(url)


def cases_for_state():
    url = 'https://brasil.io/api/dataset/covid19/caso/data/?format=json&place_type=state&is_last=True'
    return get_request_ultimos_dados(url)


def new_confirmed_for_state():
    url = 'https://brasil.io/api/dataset/covid19/caso_full/data/?format=json&place_type=state&is_last=True'
    return get_request_data_new_cases_for_state(url)


class Index(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = CasosPorCidadePiaui.objects.all()
        data_brasil_sum = cases_for_state()
        data_new_confirmed = new_confirmed_for_state()

        context['casos_por_cidades'] = queryset
        context['soma_obitos_por_cidade'] = sum([cidade.obitos for cidade in queryset])
        context['soma_casos_por_cidade'] = sum([cidade.casos for cidade in queryset])
        context['casosConfirmados'] = casos_confirmados()
        context['historicoMortes'] = historico_mortes()
        context['novosCasos'] = novos_casos()
        context['casos_por_estado'] = get_casos_por_estado(data_brasil_sum)
        context['soma_obitos_brasil'] = soma_obitos_brasil(data_brasil_sum)
        context['soma_casos_brasil'] = soma_casos_brasil(data_brasil_sum)
        context['new_cases_for_state'] = new_cases_for_state(data_new_confirmed)
        context['new_deaths_for_state'] = new_deaths_for_state(data_new_confirmed)
        context['deaths_for_state'] = deaths_for_state(data_new_confirmed)
        return context


class Upload(TemplateView):
    template_name = 'importar_csv.html'

    def post(self, request):
        file = request.FILES['arquivo'].read().decode('utf-8')
        cidades = file.replace('\r', '').split('\n')
        book = []
        for linha in cidades:
            with contextlib.suppress(ValueError):
                nome, idibge, casos, mortes = linha.split(',')
                book.append(CasosPorCidadePiaui(name=nome, idIBGE=idibge, casos=casos, obitos=mortes))

        if CasosPorCidadePiaui.objects.all().count() == 0:
            CasosPorCidadePiaui.objects.bulk_create(book)
        else:
            CasosPorCidadePiaui.objects.bulk_update(book, fields=['casos', 'obitos'])
        return redirect('index')
