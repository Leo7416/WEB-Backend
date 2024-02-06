from datetime import date
from django.shortcuts import render

data = [
            {'title': 'г.Москва, ул.Большевиков 16, частный дом', 'id': 1, 'image': 'images/1.jpg', 'text': '02234678'},
            {'title': 'г.Москва, ул.Карла Либкнехта 2, частный дом', 'id': 2, 'image': 'images/2.jpg', 'text': '06454798'},
            {'title': 'г.Липецк, ул.Кузьминская 11, частный дом', 'id': 3, 'image': 'images/3.jpg', 'text': '04281579'},
        ]

def GetOrders(request):
    return render(request, 'orders.html', {'data': data})

def GetOrder(request, id):
    for my_dict in data:
        if my_dict['id'] == id:
            print(my_dict['title'])
            return render(request, 'order.html', {'order': my_dict})
        
def GetQuery(request):
    query = request.GET.get('query', '')
    new_street = []
    for order in data:
        if query.lower() in order["title"].lower():
            new_street.append(order)

    if len  (new_street)>0:
        return render(request, 'orders.html',{'data': new_street})
    else:
        return render(request, 'orders.html', {'data': data})

