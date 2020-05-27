#
# Copyright 2020 Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import os
import shutil
from importlib import import_module
from unittest import TestCase

from nise.yaml_generators.aws import generator
from nise.yaml_generators.aws.ec2_instance_types import INSTANCE_TYPES as EC2_INSTANCE_TYPES
from nise.yaml_generators.aws.rds_instance_types import INSTANCE_TYPES as RDS_INSTANCE_TYPES


FILE_DIR = os.path.dirname(os.path.abspath(__file__))
GEN_FILE_DIR = os.path.dirname(os.path.abspath(generator.__file__))
CACHE_PATH = os.path.join(os.path.dirname(GEN_FILE_DIR), "__pycache__")


class AWSGeneratorTestCase(TestCase):
    """
    Base TestCase class, sets up a CLI parser
    """

    @classmethod
    def setUpClass(cls):
        if os.path.exists(CACHE_PATH):
            shutil.rmtree(CACHE_PATH)

        cls.module = import_module("nise.yaml_generators.aws.generator")
        cls.yg = cls.module.AWSGenerator()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(CACHE_PATH):
            shutil.rmtree(CACHE_PATH)

    def test_default_config(self):
        """Test default configuration."""
        dc = self.yg.default_config()
        self.assertTrue(isinstance(dc, self.module.dicta))
        self.assertTrue(self.yg.validate_config(dc))

    def test_config_validator(self):
        """Test config validation """
        dc = self.yg.default_config()
        self.assertTrue(self.yg.validate_config(dc))
        with self.assertRaises(TypeError):
            dc.start_date = ""
            self.assertFalse(self.yg.validate_config(dc))

    def test_dicta(self):
        """
        Test dicta class
        """
        td = self.module.dicta()
        self.assertEqual(len(td), 0)

        td.test = 1
        self.assertEqual(len(td), 1)
        self.assertEqual(td.test, td["test"])

        td.test = 2
        self.assertEqual(td.test, 2)

        td2 = td.copy()
        self.assertTrue(isinstance(td2, self.module.dicta))
        self.assertEqual(td2, td)

        with self.assertRaises(KeyError):
            td.x

        del td.test
        self.assertEqual(len(td), 0)

    def test_word_generator(self):
        """
        Test the raw word generator
        """
        dc = self.yg.default_config()
        txt = self.module.generate_words(dc)
        self.assertEqual(len(txt.split("-")), dc.max_name_words)

    def test_number_str_generator(self):
        """
        Test the raw number string generator
        """
        dc = self.yg.default_config()
        txt = self.module.generate_number_str(dc)
        self.assertTrue(txt.isdigit())
        self.assertEqual(len(txt), dc.max_resource_id_length)

    def test_generate_name(self):
        """
        Test the name generator
        """
        dc = self.yg.default_config()
        name = self.module.generate_name(dc)
        self.assertEqual(len(name.split("-")), dc.max_name_words)
        self.assertFalse(name.isdigit())
        prefix = "___"
        suffix = "^^^"
        name = self.module.generate_name(dc, prefix=prefix)
        self.assertTrue(name.startswith(prefix + "-"))
        self.assertTrue(len(name) - len(prefix + "-") > 0)
        name = self.module.generate_name(dc, prefix=prefix, suffix=suffix)
        self.assertTrue(name.startswith(prefix + "-"))
        self.assertTrue(name.endswith("-" + suffix))
        self.assertTrue(len(name.replace(prefix + "-", "").replace("-" + suffix, "")) > 0)
        name = self.module.generate_name(dc, prefix=prefix, suffix=suffix, dynamic=False)
        self.assertTrue(name.startswith(prefix + "-"))
        self.assertTrue(name.endswith("-" + suffix))
        self.assertTrue("--" not in name)
        self.assertEqual(len(name.replace(prefix + "-", "").replace(suffix, "")), 0)

    def test_generate_resource_id(self):
        """ Test resource id generation """
        dc = self.yg.default_config()
        res_id = self.module.generate_resource_id(dc)
        self.assertEqual(len(res_id), dc.max_resource_id_length)
        self.assertTrue(res_id.isdigit())

    def test_generate_tags(self):
        """
        Test label string generator
        """
        dc = self.yg.default_config()
        for key in self.module.RESOURCE_TAG_COLS.keys():
            with self.subTest(key=key):
                tags = self.module.generate_tags(key, dc)
                self.assertEqual(len(tags), len(self.module.RESOURCE_TAG_COLS[key]))
                for tag in tags:
                    self.assertTrue(tag.get("key") in self.module.RESOURCE_TAG_COLS[key])

    def test_build_data(self):  # noqa: C901
        """
        Test create data static and random
        """

        def check_exact(val, config_val, **kwargs):
            return val == config_val

        def check_range(val, config_val, v_min=1):
            return v_min <= val <= config_val

        def validate_data(data, config, check_func):
            data_transfer_gens_keys = sorted(["start_date", "end_date", "resource_id", "tags"])
            ebs_gens_keys = sorted(["start_date", "end_date", "tags"])
            ec2_gens_keys = sorted(
                [
                    "start_date",
                    "end_date",
                    "resource_id",
                    "tags",
                    "processor_arch",
                    "product_sku",
                    "region",
                    "instance_type",
                ]
            )
            rds_gens_keys = sorted(
                [
                    "start_date",
                    "end_date",
                    "resource_id",
                    "tags",
                    "processor_arch",
                    "product_sku",
                    "region",
                    "instance_type",
                ]
            )
            route53_gens_keys = sorted(["start_date", "end_date", "tags"])
            s3_gens_keys = sorted(["start_date", "end_date", "tags"])
            vpc_gens_keys = sorted(["start_date", "end_date", "tags"])

            self.assertTrue(isinstance(data, self.module.dicta))

            self.assertTrue(check_func(len(data.data_transfer_gens), config.max_data_transfer_gens))
            self.assertTrue(check_func(len(data.ebs_gens), config.max_ebs_gens))
            self.assertTrue(check_func(len(data.ec2_gens), config.max_ec2_gens))
            self.assertTrue(check_func(len(data.rds_gens), config.max_rds_gens))
            self.assertTrue(check_func(len(data.route53_gens), config.max_route53_gens))
            self.assertTrue(check_func(len(data.s3_gens), config.max_s3_gens))
            self.assertTrue(check_func(len(data.vpc_gens), config.max_vpc_gens))

            for gen in data.data_transfer_gens:
                self.assertEqual(sorted(gen.keys()), data_transfer_gens_keys)
                self.assertTrue(isinstance(gen.start_date, str) and isinstance(gen.end_date, str))
                self.assertTrue(gen.resource_id is not None)
            for gen in data.ebs_gens:
                self.assertEqual(sorted(gen.keys()), ebs_gens_keys)
                self.assertTrue(isinstance(gen.start_date, str) and isinstance(gen.end_date, str))

            list_inst_types = [d.get("inst_type") for d in EC2_INSTANCE_TYPES]
            for gen in data.ec2_gens:
                self.assertEqual(sorted(gen.keys()), ec2_gens_keys)
                self.assertTrue(isinstance(gen.start_date, str) and isinstance(gen.end_date, str))
                self.assertTrue(gen.resource_id is not None)
                self.assertTrue(gen.instance_type.get("inst_type") in list_inst_types)

            list_inst_types = [d.get("inst_type") for d in RDS_INSTANCE_TYPES]
            for gen in data.rds_gens:
                self.assertEqual(sorted(gen.keys()), rds_gens_keys)
                self.assertTrue(isinstance(gen.start_date, str) and isinstance(gen.end_date, str))
                self.assertTrue(gen.resource_id is not None)
                self.assertTrue(gen.instance_type.get("inst_type") in list_inst_types)

            for gen in data.route53_gens:
                self.assertEqual(sorted(gen.keys()), route53_gens_keys)
                self.assertTrue(isinstance(gen.start_date, str) and isinstance(gen.end_date, str))

            for gen in data.s3_gens:
                self.assertEqual(sorted(gen.keys()), s3_gens_keys)
                self.assertTrue(isinstance(gen.start_date, str) and isinstance(gen.end_date, str))

            for gen in data.vpc_gens:
                self.assertEqual(sorted(gen.keys()), vpc_gens_keys)
                self.assertTrue(isinstance(gen.start_date, str) and isinstance(gen.end_date, str))

        dc = self.yg.default_config()

        data = self.yg.build_data(dc, False)
        validate_data(data, dc, check_exact)

        data = self.yg.build_data(dc, True)
        validate_data(data, dc, check_range)