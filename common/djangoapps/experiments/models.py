#coding: utf-8
from django.db import models
from django.contrib.auth.models import User

"""
  by: Jacinto José Franco
  Este aquivo contem todas as entidades necessarias para fazer com que os experimentos randomizados funcionem
"""

class StrategyRandomization(models.Model):
    """
    Esta entidade armazena as definições das estratégias de randomização dos experimentos,
    o que possibilita mudar do algoritmo (Operador do PlanOut) e também definir um Design
    do experimento personalizado.
    """
    # Strategy: Uniform, WeightedChoice, BernoulliTrial, RandomInteger, Block Randomization
    strategyType = models.CharField(max_length=50)

    # Lista de percents do WeightedChoice
    percents = models.CharField(max_length=50, null=True)

    # PlanoutScript
    planoutScript = models.TextField(blank=True, null=True)
    planoutJson = models.TextField(blank=True, null=True)

    # Customizada --campo gerado por softwares como o JMP, SAS e R, o que possibilita criar todo tipo de randomização
    customDesign = models.TextField(blank=True, null=True)

class ExperimentDefinition(models.Model):
    """
    Esta entidade permite armazenar as definições dos experimentos, onde uma linha correspondente a um experimento de uma semana do edX.
    """

    descricao = models.CharField(max_length=60, default='meuprimeiroexperimento') # descricao do ExperimentoDeverei gerar um número ou data para a descrição
    course = models.CharField(max_length=60)
    userTeacher = models.ForeignKey(User)

    #algoritmo = models.CharField por enquanto só será utilizado A/B, depois pensarei nos demais
    strategy = models.ForeignKey(StrategyRandomization)


class OpcoesExperiment(models.Model):
    """
    Nesta entidade grava-se as opções do experimento. Em um teste A/B são inseridas duas versões do experimento.
    SectionExp serve para identificar uma uma opção/arm no Studio, já sectionExp_url serve para identificar uma entidade no LMS.
    """
    experimento = models.ForeignKey(ExperimentDefinition)
    sectionExp = models.CharField(max_length=100)
    sectionExp_url = models.CharField(max_length=50)
    version = models.CharField(max_length=1) # A ou B # Se Não tiver A, então Esta inserido a versão versão A


class UserChoiceExperiment(models.Model):
    """
    Esta entidade serve para armazenar as versões/arms definidas pela randomização definida em StrategyRandomization e atribuída
    para cada aluno, o que permite recuperar uma versão previamente definida e manter esta versão até o término do curso.
    """
    userStudent = models.ForeignKey(User)
    versionExp = models.ForeignKey(OpcoesExperiment)
    bloco = models.IntegerField(blank=True) # VOU REMOVER
    experimento = models.ForeignKey(ExperimentDefinition)


class HistoricoQuestoes(models.Model):
    """
    Terei que retirar esta tabela, pois o edX já implementa a função do histórico. NÃO PRECISA TRADUZIR
    """
    campo = models.CharField(max_length=600)
    valor = models.CharField(max_length=600)
    usuario = models.ForeignKey(User)


class AnonyMousPost(models.Model):
    """
    Com esta tabela armazena-se os o id e o usuario dos comentários anônimos. Desta forma fica mais fácil para recuperar, pois na lista
    de retornada para o LMS não há nenhuma identificação acerta dos posts post anônimos.
    """
    user = models.IntegerField()
    commentid = models.CharField(max_length=50)