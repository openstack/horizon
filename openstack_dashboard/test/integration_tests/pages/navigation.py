#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import importlib
import json

from selenium.webdriver.common import by
import six

from openstack_dashboard.test.integration_tests import config


class Navigation(object):
    """Provide basic navigation among pages.

    * allows navigation among pages without need to import pageobjects
    * shortest path possible should be always used for navigation to
      specific page as user would navigate in the same manner
    * go_to_*some_page* method respects following pattern:
      * go_to_{sub_menu}_{pagename}page
    * go_to_*some_page* methods are generated at runtime at module import
    * go_to_*some_page* method returns pageobject
    * pages must be located in the correct directories for the navigation
      to work correctly
    * pages modules and class names must respect following pattern
      to work correctly with navigation module:
      * module name consist of menu item in lower case without spaces and '&'
      * page class begins with capital letter and ends with 'Page'

    Examples:
        In order to go to Project/Compute/Overview page, one would have to call
        method go_to_compute_overviewpage()

        In order to go to Admin/System/Overview page, one would have to call
        method go_to_system_overviewpage()

    """
    # constants
    MAX_SUB_LEVEL = 4
    MIN_SUB_LEVEL = 2
    SIDE_MENU_MAX_LEVEL = 3

    CONFIG = config.get_config()
    PAGES_IMPORT_PATH = [
        "openstack_dashboard.test.integration_tests.pages.%s"
    ]
    if CONFIG.plugin.is_plugin and CONFIG.plugin.plugin_page_path:
        for path in CONFIG.plugin.plugin_page_path:
            PAGES_IMPORT_PATH.append(path + ".%s")

    ITEMS = "_"

    CORE_PAGE_STRUCTURE = \
        {
            "Project":
                {
                    "Compute":
                        {
                            "Access & Security":
                                {
                                    ITEMS:
                                        (
                                            "Security Groups",
                                            "Key Pairs",
                                            "Floating IPs",
                                            "API Access"
                                        ),
                                },
                            "Volumes":
                                {
                                    ITEMS:
                                        (
                                            "Volumes",
                                            "Volume Snapshots"
                                        )
                                },
                            ITEMS:
                                (
                                    "Overview",
                                    "Instances",
                                    "Images",
                                )
                        },
                    "Network":
                        {
                            ITEMS:
                                (
                                    "Network Topology",
                                    "Networks",
                                    "Routers"
                                )
                        },
                    "Object Store":
                        {
                            ITEMS:
                                (
                                    "Containers",
                                )
                        },
                    "Orchestration":
                        {
                            ITEMS:
                                (
                                    "Stacks",
                                )
                        }
                },
            "Admin":
                {
                    "System":
                        {
                            "Resource Usage":
                                {
                                    ITEMS:
                                        (
                                            "Daily Report",
                                            "Stats"
                                        )
                                },
                            "System info":
                                {
                                    ITEMS:
                                        (
                                            "Services",
                                            "Compute Services",
                                            "Block Storage Services",
                                            "Network Agents",
                                            "Default Quotas"
                                        )
                                },
                            "Volumes":
                                {
                                    ITEMS:
                                        (
                                            "Volumes",
                                            "Volume Types",
                                            "Volume Snapshots"
                                        )
                                },
                            ITEMS:
                                (
                                    "Overview",
                                    "Hypervisors",
                                    "Host Aggregates",
                                    "Instances",
                                    "Flavors",
                                    "Images",
                                    "Networks",
                                    "Routers",
                                    "Defaults",
                                    "Metadata Definitions",
                                    "System Information"
                                )
                        },
                },
            "Settings":
                {
                    ITEMS:
                        (
                            "User Settings",
                            "Change Password"
                        )
                },
            "Identity":
                {
                    ITEMS:
                        (
                            "Projects",
                            "Users",
                            "Groups",
                            "Domains",
                            "Roles"
                        )
                }
        }
    _main_content_locator = (by.By.ID, 'content_body')

    # protected methods
    def _go_to_page(self, path, page_class=None):
        """Go to page specified via path parameter.

         * page_class parameter overrides basic process for receiving
           pageobject
        """
        path_len = len(path)
        if path_len < self.MIN_SUB_LEVEL or path_len > self.MAX_SUB_LEVEL:
            raise ValueError("Navigation path length should be in the interval"
                             " between %s and %s, but its length is %s" %
                             (self.MIN_SUB_LEVEL, self.MAX_SUB_LEVEL,
                              path_len))

        if path_len == self.MIN_SUB_LEVEL:
            # menu items that do not contain second layer of menu
            if path[0] == "Settings":
                self._go_to_settings_page(path[1])
            else:
                self._go_to_side_menu_page([path[0], None, path[1]])
        else:
            # side menu contains only three sub-levels
            self._go_to_side_menu_page(path[:self.SIDE_MENU_MAX_LEVEL])

        if path_len == self.MAX_SUB_LEVEL:
            # apparently there is tabbed menu,
            #  because another extra sub level is present
            self._go_to_tab_menu_page(path[self.MAX_SUB_LEVEL - 1])

        # if there is some nonstandard pattern in page object naming
        return self._get_page_class(path, page_class)(self.driver, self.conf)

    def _go_to_tab_menu_page(self, item_text):
        content_body = self.driver.find_element(*self._main_content_locator)
        content_body.find_element_by_link_text(item_text).click()

    def _go_to_settings_page(self, item_text):
        """Go to page that is located under the settings tab."""
        self.topbar.user_dropdown_menu.click_on_settings()
        self.navaccordion.click_on_menu_items(third_level=item_text)

    def _go_to_side_menu_page(self, menu_items):
        """Go to page that is located in the side menu (navaccordion)."""
        self.navaccordion.click_on_menu_items(*menu_items)

    def _get_page_cls_name(self, filename):
        """Gather page class name from path.

         * take last item from path (should be python filename
           without extension)
         * make the first letter capital
         * append 'Page'
         """
        cls_name = "".join((filename.capitalize(), "Page"))
        return cls_name

    def _get_page_class(self, path, page_cls_name):

        # last module name does not contain '_'
        final_module = self.unify_page_path(path[-1],
                                            preserve_spaces=False)
        page_cls_path = ".".join(path[:-1] + (final_module,))
        page_cls_path = self.unify_page_path(page_cls_path)
        # append 'page' as every page module ends with this keyword
        page_cls_path += "page"

        page_cls_name = page_cls_name or self._get_page_cls_name(final_module)

        module = None
        # return imported class
        for path in self.PAGES_IMPORT_PATH:
            try:
                module = importlib.import_module(path %
                                                 page_cls_path)
                break
            except ImportError:
                pass
        if module is None:
            raise ImportError("Failed to import module: " +
                              (path % page_cls_path))
        return getattr(module, page_cls_name)

    class GoToMethodFactory(object):
        """Represent the go_to_some_page method."""

        METHOD_NAME_PREFIX = "go_to_"
        METHOD_NAME_SUFFIX = "page"
        METHOD_NAME_DELIMITER = "_"

        # private methods
        def __init__(self, path, page_class=None):
            self.path = path
            self.page_class = page_class
            self._name = self._create_name()

        def __call__(self, *args, **kwargs):
            return Navigation._go_to_page(args[0], self.path, self.page_class)

        # protected methods
        def _create_name(self):
            """Create method name.

            * consist of 'go_to_subsubmenu_menuitem_page'
            """
            if len(self.path) < 4:
                path_2_name = list(self.path[-2:])
            else:
                path_2_name = list(self.path[-3:])

            name = self.METHOD_NAME_DELIMITER.join(path_2_name)
            name = self.METHOD_NAME_PREFIX + name + self.METHOD_NAME_SUFFIX
            name = Navigation.unify_page_path(name, preserve_spaces=False)
            return name

        # properties
        @property
        def name(self):
            return self._name

    # classmethods
    @classmethod
    def _initialize_go_to_methods(cls):
        """Create all navigation methods based on the PAGE_STRUCTURE."""

        def rec(items, sub_menus):
            if isinstance(items, dict):
                for sub_menu, sub_item in items.items():
                    rec(sub_item, sub_menus + (sub_menu,))
            elif isinstance(items, (list, tuple)):
                # exclude ITEMS element from sub_menus
                paths = (sub_menus[:-1] + (menu_item,) for menu_item in items)
                for path in paths:
                    cls._create_go_to_method(path)

        rec(cls.CORE_PAGE_STRUCTURE, ())
        plugin_page_structure_strings = cls.CONFIG.plugin.plugin_page_structure
        for plugin_ps_string in plugin_page_structure_strings:
            plugin_page_structure = json.loads(plugin_ps_string)
            rec(plugin_page_structure, ())

    @classmethod
    def _create_go_to_method(cls, path, class_name=None):
        go_to_method = Navigation.GoToMethodFactory(path, class_name)
        inst_method = six.create_unbound_method(go_to_method, Navigation)
        setattr(Navigation, inst_method.name, inst_method)

    @classmethod
    def unify_page_path(cls, path, preserve_spaces=True):
        """Unify path to page.

        Replace '&' in path with 'and', remove spaces (if not specified
        otherwise) and convert path to lower case.
        """
        path = path.replace("&", "and")
        path = path.lower()
        if preserve_spaces:
            path = path.replace(" ", "_")
        else:
            path = path.replace(" ", "")
        return path


Navigation._initialize_go_to_methods()
