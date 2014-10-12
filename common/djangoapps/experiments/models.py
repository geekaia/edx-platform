#coding: utf-8
from django.db import models
from django.contrib.auth.models import User

"""
  by: Jacinto José Franco
  This file contains all necessary classes to make the randomized experiments run
  
  Este aquivo contem todas as entidades necessarias para fazer com que os experimentos randomizados funcionem
"""

class StrategyRandomization(models.Model):
    """
    This class stores all strategy definitions for randomizing the experiments. This will
    allow the change in algorithm (Planot Operator) as well as the definition of the Design of a
    personalized experiment

    Esta entidade armazena as definições das estratégias de randomização dos experimentos,
    o que possibilita mudar do algoritmo (Operador do PlanOut) e também definir um Design
    do experimento personalizado.
    """
    # Strategy: Uniform, WeightedChoice, BernoulliTrial, RandomInteger, Block Randomization, full factorial design, crossover
    strategyType = models.CharField(max_length=50)

    # Lista de percents do WeightedChoice
    percents = models.CharField(max_length=50, null=True)

    # PlanoutScript
    planoutScript = models.TextField(blank=True, null=True)
    planoutJson = models.TextField(blank=True, null=True)

    # Customizada --campo gerado por softwares como o JMP, SAS e R, o que possibilita criar todo tipo de randomização
    customDesign = models.TextField(blank=True, null=True)

    # Customizada --campo gerado por softwares como o JMP, SAS e R, o que possibilita criar todo tipo de randomização
    fatorial = models.TextField(blank=True, null=True)

    #Quant. periodos que sera repetido o design. Neste caso 1 semana é um periodo
    periodos = models.CharField(max_length=1, null=True)
    periodoRel = models.ForeignKey("ExperimentDefinition", blank=True, null=True, on_delete=models.SET_NULL)


class ExperimentDefinition(models.Model):
    """
    This class allows for the storage of all experiment definitions, where a row corresponds to the experiment in a week within edX

    Esta entidade permite armazenar as definições dos experimentos, onde uma linha correspondente a um experimento de uma semana do edX.
    """

    descricao = models.CharField(max_length=60, default='meuprimeiroexperimento') # descricao do ExperimentoDeverei gerar um número ou data para a descrição
    course = models.CharField(max_length=60)
    userTeacher = models.ForeignKey(User)

    #algoritmo = models.CharField por enquanto só será utilizado A/B, depois pensarei nos demais
    strategy = models.ForeignKey(StrategyRandomization)


class OpcoesExperiment(models.Model):
    """
    This class record the experiment options. In an AB test we have two arms or two versions of the intervention. 
    SectionExp identified an arm in Studio, whereas sectionExp_url identifies an entitity in the LMS

    Nesta entidade grava-se as opções do experimento. Em um teste A/B são inseridas duas versões do experimento.
    SectionExp serve para identificar uma uma opção/arm no Studio, já sectionExp_url serve para identificar uma entidade no LMS.
    """
    experimento = models.ForeignKey(ExperimentDefinition)
    sectionExp = models.CharField(max_length=100)
    sectionExp_url = models.CharField(max_length=50)
    version = models.CharField(max_length=1) # A ou B # Se Não tiver A, então Esta inserido a versão versão A


class UserChoiceExperiment(models.Model):
    """
    This class stores all arms defined by the randomization defined under the StrategyRandomization, which is 
    attributed to each learner. This allows for a previously defined version while keeping this version until
    the end of the course.

    Esta entidade serve para armazenar as versões/arms definidas pela randomização definida em StrategyRandomization e atribuída
    para cada aluno, o que permite recuperar uma versão previamente definida e manter esta versão até o término do curso.
    """
    userStudent = models.ForeignKey(User)
    versionExp = models.ForeignKey(OpcoesExperiment)
    bloco = models.IntegerField(blank=True) # VOU REMOVER
    experimento = models.ForeignKey(ExperimentDefinition)
    group = models.IntegerField(blank=True) # Needed for Cluster Randomization Codes: 0, 1, 2.... and -1 to groups that doesn't match


class HistoricoQuestoes(models.Model):
    """
    Terei que retirar esta tabela, pois o edX já implementa a função do histórico. NÃO PRECISA TRADUZIR
    """
    campo = models.CharField(max_length=600)
    valor = models.CharField(max_length=600)
    usuario = models.ForeignKey(User)


class AnonyMousPost(models.Model):
    """
    This table stores the id and user from anonymous comments. This makes it easier to recover them, since this query
    will not return any data on the anonymous posts back to the LMS

    Com esta tabela armazena-se os o id e o usuario dos comentários anônimos. Desta forma fica mais fácil para recuperar, pois na lista
    de retornada para o LMS não há nenhuma identificação acerta dos posts post anônimos.
    """
    user = models.IntegerField()
    commentid = models.CharField(max_length=50)

class GroupsCluster(models.Model):
    grupos = models.TextField(blank=True, null=True)
    experiment = models.ForeignKey(ExperimentDefinition)
    versao = models.ForeignKey("OpcoesExperiment", blank=True, null=True, on_delete=models.SET_NULL)
