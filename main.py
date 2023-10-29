# coding:utf-8

import json
import os


def getUmlClassObject(mdj_object, uml_object):
    if mdj_object.get('_type') == 'UMLClass':
        _id = mdj_object.get('_id')
        if _id:
            uml_object[_id] = mdj_object
    elif mdj_object.get('ownedElements'):
        ownedElements = mdj_object.get('ownedElements')
        for ownedElement in ownedElements:
            getUmlClassObject(ownedElement, uml_object)


def write_umlclass_js(uml_object, uml_class_object, export_path):
    # 父类
    super_class = None
    # 获取class name
    name = uml_class_object.get('name')
    if not name:
        return
    path = export_path + name + '.js'
    # 写js文件
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n')
        # 头部注释
        f.write('/**\n')
        f.write(''' * {}\n'''.format(uml_class_object.get('documentation', '')))
        f.write(''' * @class {}\n'''.format(name))
        # 继承关系生成
        uml_chileList = uml_class_object.get('ownedElements', [])
        for item in uml_chileList:
            if item and item.get('_type') == 'UMLGeneralization':
                if item.get('target') and item.get('target').get('$ref'):
                    ref = item.get('target').get('$ref')
                    super_class_object = uml_object.get(ref)
                    if super_class_object:
                        super_class = super_class_object.get('name')
        if super_class:
            f.write(''' * @extends {}\n'''.format(super_class))
        f.write(''' * @moduleEX\n''')
        f.write(''' * @param {Object} options 构造参数\n''')
        # 默认参数
        for item in uml_class_object.get('attributes', []):
            defaultValue = item.get('defaultValue')
            defaultValueStr = ''
            if defaultValue:
                defaultValueStr = ' = ' + defaultValue
            str = ' * @param {' + item.get('type', '') + '} ' + '[options.' + item.get(
                'name') + defaultValueStr + '] ' + item.get('documentation', '') + '\n'
            f.write(str)
        f.write(' */\n')
        # class类主体
        f.write('''class {} {}'''.format(name, 'extends ' + super_class + ' ' if super_class else '') + '{\n')
        # 开始构造
        f.write('  constructor(options) {\n')
        if super_class:
          f.write('    super(options)\n')
        f.write('    options = defaultValue(options, {})\n')
        # 绘制中间段构造成员参数
        write_class_attributes(f, uml_class_object.get('attributes', []), name)
        f.write('  }\n')
        # 结束构造
        f.write('\n')
        # 开始计算方法
        write_class_operations(f, uml_class_object.get('operations', []), uml_class_object.get('attributes', []), name)
        f.write('}\n')
        # class类主体结束
        f.write('\n')
        f.write('''export default {}\n'''.format(name))


def write_class_attributes(f, attributes, class_name):
    for attribute in attributes:
        name = attribute.get('name', '')
        isStatic = attribute.get('isStatic')
        isReadOnly = attribute.get('isReadOnly')
        f.write('    /**\n')
        f.write('''     * {}\n'''.format(attribute.get('documentation', '')))
        if isStatic:
            f.write('''     * @static\n''')
        if isReadOnly:
            f.write('''     * @readonly\n''')
        f.write('     * @member {' + attribute.get('type', '') + '} ' + '''{}.prototype.{}'''.format(class_name,
                                                                                                     name) + '\n')
        f.write('     */\n')
        if  attribute.get('defaultValue'):
            f.write('''    this.{} = defaultValue(options.{}, {})\n'''.format(name, name,
                                                                   attribute.get('defaultValue', '''\'\'''')))
        else:
            f.write('''    this.{} = options.{}\n'''.format(name, name))


def set_operations(operations, class_name):
    for operation in operations:
        if operation:
            name = operation.get('name', '')
            if name == 'toJSON':
                operation['documentation'] = operation.get('documentation', "导出json对象")
                operation['parameters'] = [{
                    "type": "Object",
                    "direction": "return",
                    "documentation": 'json对象'
                }]
            if name == 'fromJSON':
                operation['documentation'] = operation.get('documentation', "通过json构造"+class_name+"对象")
                operation['parameters'] = [{
                    "type": class_name,
                    "direction": "return",
                    "documentation": class_name + '实例'
                }, {
                    "type": "Object",
                    "documentation": 'json对象',
                    "name":"json"
                }]
            if name == 'clone':
                operation['documentation'] = operation.get('documentation','克隆' + class_name + '对象')
                operation['parameters'] = [{
                    "type": class_name,
                    "direction": "return",
                    "documentation": '克隆后的' + class_name + '实例'
                }]


def write_class_operations(f, operations, attributes, class_name):
    set_operations(operations, class_name)
    for operation in operations:
        isStatic = operation.get('isStatic')
        parameters = operation.get('parameters', [])
        f.write('''  /**\n''')
        f.write('''   * {}\n'''.format(operation.get('documentation', '函数')))
        returnParamter = None
        # 参数
        param_list = []
        for parameter in parameters:
            if parameter.get('direction') and parameter.get('direction') == 'return':
                returnParamter = parameter
            elif parameter.get('name'):
                param_list.append(parameter.get('name'))
                f.write('''   * @param {} {} {}\n'''.format('{' + parameter.get('type', 'any') + '}',
                                                            parameter.get('name', ''),
                                                            parameter.get('documentation', '')))
        # 返回值
        if returnParamter:
            f.write('''   * @return {} {}\n'''.format('{' + returnParamter.get('type', 'any') + '}',
                                                      returnParamter.get('documentation', '')))
        f.write('''   */\n''')
        # 函数定义第一行
        func_first_str = '  static ' if isStatic else '  '
        func_first_str = func_first_str + operation.get('name', '')
        parameter_str = ''
        for p in param_list:
            parameter_str = parameter_str + p + ', '
        if parameter_str:
            parameter_str = parameter_str[:-2]
        func_first_str = func_first_str + '''({})'''.format(parameter_str)
        func_first_str = func_first_str + " {\n"
        f.write(func_first_str)
        # 函数内容（一般情况下不会写函数体，对于几类常用函数写函数体）
        if operation.get('name', '') == 'toJSON':
            f.write('''    const json = super.toJSON()\n''')
            for attribute in attributes:
                f.write('''    json.{} = this.{}\n'''.format(attribute.get('name', ''), attribute.get('name', '')))
            f.write('''    return json\n''')
        if operation.get('name', '') == 'fromJSON':
            f.write('''    json = defaultValue(json, {})\n''')
            f.write('''    return new {}(json)\n'''.format(class_name))
        if operation.get('name', '') == 'clone':
            f.write('''    return new {}(this.toJSON())\n'''.format(class_name))
        f.write("  }\n")
        f.write('''\n''')


def parse_mdj(mdj_path, export_path):
    with open(mdj_path, 'r', encoding='utf-8') as f:
        mdj = json.load(f)
        uml_object = {}
        getUmlClassObject(mdj, uml_object)
        for v in uml_object:
            write_umlclass_js(uml_object, uml_object.get(v), export_path)


if __name__ == "__main__":
    # 查询当前目录下所有的mdj文件
    dirs = os.listdir('./')
    export_dir_names = []
    for dir in dirs:
        if dir.find('.mdj') > -1:
            export_dir_names.append(dir.split('.mdj')[0])
    # 解析mdj文件
    for export_dir_name in export_dir_names:
        js_path = './' + export_dir_name
        if not os.path.isdir(js_path):
            os.mkdir(js_path)
        parse_mdj(js_path + '.mdj', js_path + '/')
