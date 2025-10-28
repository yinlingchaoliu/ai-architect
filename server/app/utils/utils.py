import json
from dataclasses import fields ,asdict,MISSING
from urllib.parse import parse_qs
from typing import get_type_hints

def json_to_dataclass(json_str: str, data_class):
        """将 JSON 字符串转换为 dataclass 对象"""
        data = json.loads(json_str)
        # 获取 dataclass 的所有字段名
        class_fields = {f.name for f in fields(data_class)}
        # 过滤掉 data_class 中不存在的字段
        filtered_data = {k: v for k, v in data.items() if k in class_fields}
        return data_class(**filtered_data)

def to_dict(data_class):
    """将 dataclass 对象转换为字典"""
    return asdict(data_class)

class QueryStringConverter:
    def query_string_to_dataclass(self, query_str: str, data_class):        
        # 解析查询字符串
        parsed_data = parse_qs(query_str)
        
        # 将列表值转换为单个值（如果只有一个元素）
        data = {}
        for key, value in parsed_data.items():
            if len(value) == 1:
                data[key] = value[0]
            else:
                data[key] = value
        
        # 获取 dataclass 的所有字段信息
        class_fields = {f.name: f for f in fields(data_class)}
        type_hints = get_type_hints(data_class)
        
        # 构建完整的数据字典，包含所有必需字段
        complete_data = {}
        
        for field_name, field in class_fields.items():
            if field_name in data:
                # 字段存在于查询字符串中，尝试类型转换
                value = data[field_name]
                field_type = type_hints.get(field_name)
                try:
                    # 根据字段类型转换值
                    converted_value = self.convert_value(value, field_type)
                    complete_data[field_name] = converted_value
                except (ValueError, TypeError) as e:
                    # 类型转换失败，使用默认值
                    print(f"警告: 字段 '{field_name}' 的值 '{value}' 无法转换为 {field_type}，使用默认值")
                    complete_data[field_name] = self.get_default_value(field, field_type)
            else:
                # 字段不存在于查询字符串中，使用默认值
                complete_data[field_name] = self.get_default_value(field, type_hints.get(field_name))
        
        return data_class(**complete_data)
    
    def convert_value(self, value, target_type):
        """
        将字符串值转换为目标类型
        """
        if value is None:
            return None
        
        # 如果已经是目标类型，直接返回
        if target_type is None or isinstance(value, target_type):
            return value
        
        # 处理 Optional 类型
        origin = getattr(target_type, '__origin__', None)
        if origin is not None:
            # 对于 Optional[X]，获取实际类型
            args = getattr(target_type, '__args__', [])
            non_none_types = [t for t in args if t is not type(None)]
            if non_none_types:
                return self.convert_value(value, non_none_types[0])
        
        # 基本类型转换
        if target_type is int:
            return int(value)
        elif target_type is float:
            return float(value)
        elif target_type is bool:
            # 处理布尔值
            if isinstance(value, str):
                lower_val = value.lower()
                if lower_val in ('true', 'yes', '1', 'on'):
                    return True
                elif lower_val in ('false', 'no', '0', 'off'):
                    return False
            return bool(value)
        elif target_type is str:
            return str(value)
        else:
            # 对于其他类型，尝试直接构造
            try:
                return target_type(value)
            except (TypeError, ValueError):
                # 如果无法转换，返回原始值
                return value
    
    def get_default_value(self, field, field_type):
        """
        获取字段的默认值
        """
        # 优先使用字段定义的默认值
        if field.default is not MISSING:
            return field.default
        elif field.default_factory is not MISSING:
            return field.default_factory()
        
        # 根据类型提供合适的默认值
        type_defaults = {
            int: 0,
            float: 0.0,
            str: "",
            bool: False,
            list: [],
            dict: {},
        }
        
        # 如果是已知的基本类型，返回对应的默认值
        for base_type, default_val in type_defaults.items():
            if field_type is base_type:
                return default_val
        
        # 对于其他类型，尝试创建实例
        try:
            return field_type()
        except:
            # 如果无法创建实例，返回 None
            return None


def query_string_to_dataclass(query_str, dataclass):
    qs_instance = QueryStringConverter()
    return qs_instance.query_string_to_dataclass(query_str, dataclass)