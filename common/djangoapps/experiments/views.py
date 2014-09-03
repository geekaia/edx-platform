# -*- coding: utf-8 -*-

from __future__ import absolute_import

from django.views.decorators.http import require_GET
import logging
from uuid import uuid4
from django.core.exceptions import PermissionDenied

from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods
import datetime

from edxmako.shortcuts import render_to_response
from django_future.csrf import ensure_csrf_cookie
from xmodule.modulestore.django import modulestore, loc_mapper
from xmodule.modulestore.inheritance import own_metadata
# from xmodule.modulestore.locator import BlockUsageLocator
from xmodule.modulestore import Location
from util.json_request import expect_json, JsonResponse
from contentstore.utils import get_modulestore, get_lms_link_for_item
from contentstore.views.access import has_course_access

from experiments.models import *
from models.settings.course_grading import CourseGradingModel

from contentstore.utils import compute_publish_state
from contentstore.views.helpers import _xmodule_recurse

from django.http import HttpResponse
import csv

from experiments.models import *
from django.contrib.auth.decorators import login_required


# New EDX
from opaque_keys.edx.keys import UsageKey, CourseKey

from django_future.csrf import ensure_csrf_cookie
from django.core.context_processors import csrf

from experiments.models import *

# from contentstore.utils import (
#     get_lms_link_for_item, add_extra_panel_tab, remove_extra_panel_tab,
#     get_modulestore)


__all__ = ['experiments_handler', 'block_clone_handler', 'analise_experiment', 'EmailsExp', 'DefineStrategy']
CREATE_IF_NOT_FOUND = ['course_info']
log = logging.getLogger(__name__)

@require_GET
@login_required
def EmailsExp(request,  course_key_string, idExp=None):
    """
    Retorna a lista de e-mails por ARM, o que pode permitir que o professor envie e-mails para um grupo em específico.

    :param request: httprequest default
    :param idExp: ID do experimento
    :return: CSV file format
    """


    # usage_key = CourseKey.from_string(course_key_string)
    #
    # # print "Course Location: ", courseKey
    #
    # if not has_course_access(request.user, usage_key):
    #     raise PermissionDenied()

    usage_key = CourseKey.from_string(course_key_string)

    if not has_course_access(request.user, usage_key):
        raise PermissionDenied()

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="relatorio2.csv"'
    writer = csv.writer(response)

    try:
        exp = ExperimentDefinition.objects.get(userTeacher=request.user, id=idExp)
        expsUsrsInfos={}

        uschs = UserChoiceExperiment.objects.filter(experimento=exp)

        print "Tamanho: ", len(uschs)
        # print "exp: ", exp

        listA = []
        listB = []
        listC = []

        writer.writerow(['arm', 'usuario', 'e-mail'])

        for usch in uschs:
            if usch.versionExp.version == "A":
                listA.append(usch.userStudent)
            elif usch.versionExp.version == "B":
                listB.append(usch.userStudent)
            else:
                listC.append(usch.userStudent)

        for i in listA:
            writer.writerow(['A', i.username, i.email])

        for i in listB:
            writer.writerow(['B', i.username, i.email])

        for i in listC:
            writer.writerow(['C', i.username, i.email])

        return response

    except:
        print "Erro ao pegar o exp"


@ensure_csrf_cookie
@login_required
def DefineStrategy(request,  course_key_string, idExperiment=None):

    """
    Permite alternar entre os operadores do PlanOut e permite especificar um design do experimento criado pelo JMP, R ou Minitab.

    :param request:
    :param course_key_string:
    :param idExperiment: id do experimento
    :return: renderiza a página que pemrite definir a estratégia
    """


    mensagem = ""
    mensagemBlock=''
    mensagemWeightedChoice = ''
    mensagemUniformChoice=''
    mensagemCustom=''

    usage_key = CourseKey.from_string(course_key_string)

    # print "Course Location: ", courseKey

    if not has_course_access(request.user, usage_key):
        raise PermissionDenied()

    csrf_token = csrf(request)['csrf_token']

    exp = ExperimentDefinition.objects.get(pk=idExperiment)

    strategy = exp.strategy

    try:

        if request.POST:
            print "Ola mundo cruel!!!"

            strategySel = request.POST['strategySel']


            print "O que está na memória!!!:", strategySel, ' len:', len(strategySel)

            strategy.strategyType = strategySel


            if strategySel == 'WeightedChoice':

                # monta os percents
                fields = strategy.percents.split(';')
                cont = 0

                maxl = len(fields)
                lista = []

                for i in range(0, maxl):
                    lista.append(str(request.POST['peso'+str(i)]))


                strategy.percents = ';'.join(lista)
                strategy.save()

                mensagemWeightedChoice = "WeightedChoice Salvo!"
            elif strategySel == 'planOut':

                # Este Design ainda não está funcionando apropriadamente
                strategy.planoutScript = request.POST['input']
                strategy.planoutJson = request.POST['output']
                strategy.save()

                mensagemCustom = 'PlanoutScript e Json salvos com sucesso!!'

            elif strategySel == 'UniformChoice':
                strategy.save()

                print "A estratégia é UniformChoice"
                mensagemUniformChoice = "UniformChoice Salvo!"

            elif strategySel == 'customdesign':
                strategy.customDesign = request.POST['customDesign']
                strategy.save()

    except:
        mensagem = 'Ocorreu um erro ao salvar a estratégia!!!'

    pesos = "<br />"
    arms = ['A', 'B', 'C', 'D', 'D', 'F']

    # Render html pesos Weight
    cont = 0
    # Pega a quantidade de versões
    #OpcoesExperiment.objects.filter(experimento=exp.)
    percents = strategy.percents.split(';')

    for peso in percents:
        pesos += "Percent Arm "+arms[cont]+" <input type='text' name='peso"+str(cont)+"' class='form-control' value='"+str(peso)+"' /> <br />"
        cont += 1

    return render_to_response('experiment/estrategia.html', {
            'course_key_string': course_key_string,
            'csrf': csrf_token,
            'idExperiment': idExperiment,
            'strat': strategy,
            'elementosStrat': '',
            'pesos': pesos,
            'mensagem': mensagem,
            'mensagemBlock': mensagemBlock,
            'mensagemWeightedChoice': mensagemWeightedChoice,
            'mensagemUniformChoice': mensagemUniformChoice,
            'mensagemCustom': mensagemCustom,
        })


@require_GET
@ensure_csrf_cookie
@login_required
def experiments_handler(request, course_key_string):
    """
    Mostra a listagem dos experimentos deste curso

    :param request:
    :param course_key_string:
    :return:
    """

    usage_key = CourseKey.from_string(course_key_string)
    if not has_course_access(request.user, usage_key):
        raise PermissionDenied()

    course_module = modulestore().get_course(usage_key, depth=3)

    # Lista dos Experimentos
    expList = ExperimentDefinition.objects.filter(userTeacher=request.user, course=course_module.location)
    lms_link = get_lms_link_for_item(course_module.location) # link para o LMS

    return render_to_response('experiment/experimentos.html', {
            'lms_link': lms_link,
            'explist': expList,
            'course_key_string': course_key_string,
            'context_course': course_module # Se não tiver essa variável não carregará o menu
        })


@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "PUT", "POST"))
@expect_json
def block_clone_handler(request, course_key_string):
    """
    Permite clonar o conteúdo de uma dada semana do experimento. Além de clonar nesta função faz a definição do experimento. o que insere entradas nas
    tabelas

    :param request:
    :param course_key_string:
    :return:
    """

    if request.method in ('PUT', 'POST'):
        #  Get location Course com base no valor passado pelo Json
        locatorCursokey = UsageKey.from_string(request.json['parent_locator'])
        locatorSectionKey = UsageKey.from_string(request.json['source_locator'])

        if not has_course_access(request.user, locatorSectionKey):
            raise PermissionDenied()

        # Verifica se já tem um experimento de acordo com o SourceLocation
        expSection = None
        try:
            opcExp = OpcoesExperiment.objects.get(sectionExp='%s' % request.json['source_locator'])
            temExp = True
            expSection = opcExp.experimento # pega o experimento para cadastrar a nova versao
        except:
            temExp = False

        # Pesquisa no banco de dados o Curso do qual duplicará os módulos
        course = modulestore().get_item(locatorCursokey, depth=3)
        sections = course.get_children()
        quantidade = 0

        for section in sections:
            # section_locator = loc_mapper().translate_location(course.location.course_id, section.location, False, True)
            print "<<<<<<<<<<< --------------->>>>>>>"
            print "section: LOCATION    ", section.location
            print "Seção Find: ", locatorSectionKey # Confusão translate_location pega o locator e locator_to_location pega o location
            print "<<<<<<<<<<< --------------->>>>>>>"

            if locatorSectionKey == section.location:
                NewLocatorItemSection = create_item(locatorCursokey, 'chapter', section.display_name_with_default, request)

                print "New Location item: ", unicode(NewLocatorItemSection)
                print "section.start: ", section.start
                print "section locator: ", NewLocatorItemSection

    #             # tem que Mudar para HomeWork, ou qualquer tipo que eu definir
                SectionLocation =  NewLocatorItemSection
    #
                print "Course Location: ", NewLocatorItemSection
                descript = get_modulestore(NewLocatorItemSection).get_item(NewLocatorItemSection)
                print "Descript: ", descript

    #             # Start Value
                storeSection = get_modulestore(NewLocatorItemSection)
    #
                try:
                    existing_item = storeSection.get_item(SectionLocation)

                    field = existing_item.fields['start']

                    if section.start is not None:
                        print "NÃO É NULO "
                        field.write_to(existing_item, section.start)

                        storeSection.update_item(existing_item, request.user.id)

                except:
                    print "Start Date and end Date"


                subsections = section.get_children()
                quantidade = 0


                # Aqui adiciona o campo do Experimento e a versão que pertence
                # neste caso, utilizaremos A e B

                # Será adicionado os campos EXPERIMENTO e VERSÃO do EXPERIMENTO no campo da Section


                # Verifique se há um experimento para este location
                # Se tiver, retorna o objeto experimento experimento

                if temExp:
                    opcExp3 = OpcoesExperiment()
                    opcExp3.experimento = expSection
                    opcExp3.sectionExp = "%s" % NewLocatorItemSection
                    opcExp3.sectionExp_url = '%s' % getURLSection(locatorCursokey, NewLocatorItemSection)
                    opcExp3.version = 'C'
                    opcExp3.save()

                    st = opcExp3.experimento.strategy
                    st.percents +=';0.0'
                    st.save()

                else:
                    st = StrategyRandomization()
                    st.strategyType = 'UniformChoice'
                    st.percents = '0.0;0.0'
                    st.probability = 0.0
                    st.quantAlunos = 0
                    st.tamanhoBlocos = 0
                    st.quantBlocos = 0
                    st.save()

                    # Experiment defintion
                    exp = ExperimentDefinition()
                    exp.course = request.json['parent_locator']
                    exp.userTeacher = request.user
                    exp.status = 'paused'
                    now = datetime.datetime.now()
                    exp.descricao='MyExperiment %s ' % now
                    exp.strategy = st
                    exp.save()

                    # Define a primeira versão do experimento
                    opcExp = OpcoesExperiment()
                    opcExp.experimento = exp
                    opcExp.sectionExp = "%s" % locatorSectionKey
                    opcExp.sectionExp_url = "%s" % section.url_name
                    opcExp.version = 'A'
                    opcExp.save()

                    # Define a segunda versão do experimento
                    opcExp2 = OpcoesExperiment()
                    opcExp2.experimento = exp
                    opcExp2.sectionExp = "%s" % NewLocatorItemSection
                    opcExp2.sectionExp_url = '%s' % getURLSection(locatorCursokey, NewLocatorItemSection)
                    opcExp2.version = 'B'
                    opcExp2.save()

                for subsection in subsections:
                    print
                    print
                    print "Clonando SubSeção: ", subsection.location

                    NewLocatorItemSubsection = create_item(NewLocatorItemSection, 'sequential', subsection.display_name_with_default, request)

                    # Agora iremos testar os Units
                    units_Subsection = subsection.get_children()


                    print "Information about the subsection: "
                    print "subsection.format: ", subsection.format
                    print "subsection.start: ", subsection.start
                    print "Subsection locator: ", NewLocatorItemSubsection

                    # tem que Mudar para HomeWork, ou qualquer tipo que eu definir
                    # subLocation = loc_mapper().translate_locator_to_location(NewLocatorItemSubsection)

                    # print "vert Location: ", subLocation
                    # old_location = course_location.replace(category='course_info', name=block)
                    #
                    #
                    descript = get_modulestore(NewLocatorItemSubsection).get_item(NewLocatorItemSubsection)
                    print "Descript: ", descript

                    CourseGradingModel.update_section_grader_type(descript, subsection.format, request.user)

                    # Start Value
                    storeSection = get_modulestore(NewLocatorItemSubsection)

                    try:
                        existing_item = storeSection.get_item(NewLocatorItemSubsection)

                        field = existing_item.fields['start']

                        if subsection.start is not None:
                            print "NÃO É NULO "
                            field.write_to(existing_item, subsection.start)

                            storeSection.update_item(existing_item, request.user.id)

                    except:
                        print "Deu erro"

                    # Print all Units
                    for unit in units_Subsection:

                        originalState = compute_publish_state(unit)
                        destinationUnit = duplicate_item(NewLocatorItemSubsection, unit.location, unit.display_name_with_default, request.user)


                        # Nesta parte faz-se a leitura se e privado ou publico, se publico, seta a variavel como publico
                        try:

                            print "Vou fazer o translation -- destinationUnit ", destinationUnit

                            # unitLocation = loc_mapper().translate_locator_to_location(destinationUnit)
                            unitLocation = destinationUnit
                            print "unity location: ", unitLocation


                            # Start Value
                            storeUnit = get_modulestore(unitLocation)
                            print "STORE UNIT"

                            try:
                                existing_itemUnit = storeUnit.get_item(unitLocation)

                            except:
                                print "Deu erro"

                            print "Antes do public"

                            if originalState == 'public':
                                def _publish(block):
                                    # This is super gross, but prevents us from publishing something that
                                    # we shouldn't. Ideally, all modulestores would have a consistant
                                    # interface for publishing. However, as of now, only the DraftMongoModulestore
                                    # does, so we have to check for the attribute explicitly.
                                    store = get_modulestore(block.location)
                                    print "Peguei o Store"

                                    if hasattr(store, 'publish'):
                                        store.publish(block.location, request.user.id)

                                _xmodule_recurse(
                                    existing_itemUnit,
                                    _publish
                                )



                        except:
                            print "Erro ao setar publico"

    dataR = {'ok': quantidade }
    #
    return JsonResponse(dataR)



def getURLSection(course_location, loc):
    curso = modulestore().get_item(course_location, depth=3)
    sections = curso.get_children()

    print "LOC ", loc

    for section in sections:

        if section.location == loc:
            print "Url Name1: ", section.url_name
            return section.url_name
#
#
# def getMetadata(parent_location, duplicate_source_location, parent_destination, display_name=None, user=None):
#     """
#     Duplicate an existing xblock as a child of the supplied parent_location.
#     """
#
#     # print "parent_location: ", parent_location
#     # print "duplicate_source_location: ", duplicate_source_location
#     # print "parent_destination: ", parent_destination
#     # print
#
#
#     print "Dp primeiro"
#     store = get_modulestore(duplicate_source_location)
#
#     print "Dp segundo -- store: ", store
#     source_item = store.get_item(duplicate_source_location)
#
#     print "Dp terceiro -- Source-item: ", source_item
#     # Change the blockID to be unique.
#     dest_location = parent_destination.replace(name=uuid4().hex)
#
#     print "Dp quarto -- Dest_location: ", dest_location
#     category = duplicate_source_location.category
#
#     print "Dp quinto -- Categoria: ", category
#
#     # Update the display name to indicate this is a duplicate (unless display name provided).
#     duplicate_metadata = own_metadata(source_item)
#
#     return duplicate_metadata, source_item.data if hasattr(source_item, 'data') else None, category

#
def create_item(parent_location, category, display_name, request, dt_metadata=None, datacomp=None):

    """
    Cria um item no mongoDB de acordo com a categoria especificada.

    :param parent_location:
    :param category: categoria do experimento sequential, chapter e vertical
    :param display_name:
    :param request:
    :param dt_metadata:
    :param datacomp:
    :return:
    """


    """View for create items."""

    print "-- Segundo -- "
    parent = get_modulestore(category).get_item(parent_location)
    print "-- Terceiro -- "
    dest_location = parent_location.replace(category=category, name=uuid4().hex)
    print "-- Quarto -- "

    if not has_course_access(request.user, parent_location):
        raise PermissionDenied()
    print "-- Quinto -- "
    # get the metadata, display_name, and definition from the request

    metadata = {}
    data = None

    if dt_metadata is not None:
        metadata = dt_metadata
        data = datacomp
    print "-- Sexto -- "

    if display_name is not None:
        metadata['display_name'] = display_name

    print "-- Sétimo -- "
    get_modulestore(category).create_and_save_xmodule(
        dest_location,
        definition_data=data,
        metadata=metadata,
        system=parent.runtime,
    )
    print "-- oitavo -- "

    # # TODO replace w/ nicer accessor
    if not 'detached' in parent.runtime.load_block_type(category)._class_tags:
        parent.children.append(dest_location) # Vamos ver se fuciona
        print "-- nono -- "
        get_modulestore(parent.location).update_item(parent, request.user.id)
        print "-- décimo -- "


    return dest_location


# # comp_locator = loc_mapper().translate_location(course.location.course_id, comp.location, False, True)
# # fonte = unit_location # parent_locator = BlockUsageLocator(request.json['parent_locator'])
# # destino = NewLocationItem # Unit duplicada da Fonte
#
# # duplicate_source_locator = comp_locator
#
#
def duplicate_item(parent_location, duplicate_source_location, display_name=None, user=None):
    """
    Duplicate an existing xblock as a child of the supplied parent_location.
    """
    print "parent_location: ", parent_location
    print "duplicate_source_location: ", duplicate_source_location
    #print "parent_destination: ", parent_destination
    print

    store = get_modulestore(duplicate_source_location)
    source_item = store.get_item(duplicate_source_location)
    # Change the blockID to be unique.
    dest_location = duplicate_source_location.replace(name=uuid4().hex)
    category = dest_location.category

    # Update the display name to indicate this is a duplicate (unless display name provided).
    duplicate_metadata = own_metadata(source_item)
    if display_name is not None:
        duplicate_metadata['display_name'] = display_name
    else:
        if source_item.display_name is None:
            # duplicate_metadata['display_name'] = _("Duplicate of {0}").format(source_item.category)
            duplicate_metadata['display_name'] = source_item.category
        else:
            duplicate_metadata['display_name'] =source_item.display_name

    get_modulestore(category).create_and_save_xmodule(
        dest_location,
        definition_data=source_item.data if hasattr(source_item, 'data') else None,
        metadata=duplicate_metadata,
        system=source_item.runtime,
    )

    dest_module = get_modulestore(category).get_item(dest_location)
    # Children are not automatically copied over (and not all xblocks have a 'children' attribute).
    # Because DAGs are not fully supported, we need to actually duplicate each child as well.
    if source_item.has_children:
        dest_module.children = []
        for child in source_item.children:
            # dupe = duplicate_item(dest_location, Location(child), user=user)
            dupe = duplicate_item(dest_location, child, user=user)
            dest_module.children.append(dupe)
        get_modulestore(dest_location).update_item(dest_module, user.id if user else None)

    if not 'detached' in source_item.runtime.load_block_type(category)._class_tags:
        parent = get_modulestore(parent_location).get_item(parent_location)
        # If source was already a child of the parent, add duplicate immediately afterward.
        # Otherwise, add child to end.
        if duplicate_source_location in parent.children:
            source_index = parent.children.index(duplicate_source_location)
            parent.children.insert(source_index + 1, dest_location)
        else:
            parent.children.append(dest_location)
        get_modulestore(parent_location).update_item(parent, user.id if user else None)

    return dest_location
