"""
Init dispatcher.protols

De uma forma resumida, protocolos da dispatcher tem a seguinte função:

1) Protocolos recebem dados brutos (via hardware ou software) 
2) Convertem para o padrão Envelope
3) Publicam o evelope no EventBus

Da mesma forma, podem fazer o caminho inverso:

1) Receber um comando para enviar dados
2) Converter o Envelope em dados brutos
3) Enviar para um Hardware/Software.
"""
