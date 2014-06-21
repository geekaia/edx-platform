#coding: utf-8
from django.db import models
from django.contrib.auth.models import User


# Esta tabela explica
class ExperimentDefinition(models.Model):
    descricao = models.CharField(max_length=255, default='meuprimeiroexperimento') # descricao do ExperimentoDeverei gerar um número ou data para a descrição
    course = models.CharField(max_length=500)
    status = models.CharField(max_length=9) # started finished paused
    userTeacher = models.ForeignKey(User)

    #algoritmo = models.CharField por enquanto só será utilizado A/B, depois pensarei nos demais


class OpcoesExperiment(models.Model):

    experimento = models.ForeignKey(ExperimentDefinition)
    sectionExp = models.CharField(max_length=500)
    sectionExp_url = models.CharField(max_length=1000)
    version = models.CharField(max_length=1) # A ou B # Se Não tiver A, então Esta inserido a versão versão A


# Esta
class UserChoiceExperiment(models.Model):
    userStudent = models.ForeignKey(User)
    versionExp = models.ForeignKey(OpcoesExperiment)
    experimento = models.ForeignKey(ExperimentDefinition)


class HistoricoQuestoes(models.Model):
    campo = models.CharField(max_length=600)
    valor = models.CharField(max_length=600)
    usuario = models.ForeignKey(User)


#             opcs = OpcoesExperiment.objects.filter(experimento=urlExp.experimento)





