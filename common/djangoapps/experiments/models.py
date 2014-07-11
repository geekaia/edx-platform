#coding: utf-8
from django.db import models
from django.contrib.auth.models import User


class StrategyRandomization(models.Model):
    # Strategy: Uniform, WeightedChoice, BernoulliTrial, RandomInteger, Block Randomization
    strategyType = models.CharField(max_length=50)
    # Caso a estrategia seja Weight
    percent1 = models.DecimalField(max_digits=2, decimal_places=2, blank=True, null=True) # Probabilidade de o bernoult trial
    percent2 = models.DecimalField(max_digits=2, decimal_places=2, blank=True, null=True) # Probabilidade de o bernoult trial
    probability = models.DecimalField(max_digits=2, decimal_places=2, blank=True, null=True) # Probabilidade de o bernoult trial

    # Blocos
    quantAlunos = models.IntegerField(blank=True, null=True) # exemplo 200 alunos
    tamanhoBlocos = models.IntegerField(blank=True, null=True) # 10
    quantBlocos = models.IntegerField(blank=True, null=True) # 200/10 = 20 tem que fazer a definição pelo javascript

    # Estratificada
    fatorList = models.CharField(max_length=600, null=True)
    quantAlunoStrats = models.IntegerField(blank=True, null=True)

    # Customizada
    planoutScript = models.TextField(blank=True, null=True)
    planoutJson = models.TextField(blank=True, null=True)


class ExperimentDefinition(models.Model):
    descricao = models.CharField(max_length=255, default='meuprimeiroexperimento') # descricao do ExperimentoDeverei gerar um número ou data para a descrição
    course = models.CharField(max_length=500)
    status = models.CharField(max_length=9) # started finished paused
    userTeacher = models.ForeignKey(User)

    #algoritmo = models.CharField por enquanto só será utilizado A/B, depois pensarei nos demais
    strategy = models.ForeignKey(StrategyRandomization)


class OpcoesExperiment(models.Model):

    experimento = models.ForeignKey(ExperimentDefinition)
    sectionExp = models.CharField(max_length=500)
    sectionExp_url = models.CharField(max_length=1000)
    version = models.CharField(max_length=1) # A ou B # Se Não tiver A, então Esta inserido a versão versão A


class UserChoiceExperiment(models.Model):
    userStudent = models.ForeignKey(User)
    versionExp = models.ForeignKey(OpcoesExperiment)
    bloco = models.IntegerField(blank=True)
    experimento = models.ForeignKey(ExperimentDefinition)


class HistoricoQuestoes(models.Model):
    campo = models.CharField(max_length=600)
    valor = models.CharField(max_length=600)
    usuario = models.ForeignKey(User)