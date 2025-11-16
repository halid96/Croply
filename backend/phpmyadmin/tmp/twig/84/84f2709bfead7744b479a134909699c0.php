<?php

use Twig\Environment;
use Twig\Error\LoaderError;
use Twig\Error\RuntimeError;
use Twig\Extension\CoreExtension;
use Twig\Extension\SandboxExtension;
use Twig\Markup;
use Twig\Sandbox\SecurityError;
use Twig\Sandbox\SecurityNotAllowedTagError;
use Twig\Sandbox\SecurityNotAllowedFilterError;
use Twig\Sandbox\SecurityNotAllowedFunctionError;
use Twig\Source;
use Twig\Template;

/* table/chart/tbl_chart.twig */
class __TwigTemplate_e93db05abd3d6d190f9633701378d0a6 extends Template
{
    private $source;
    private $macros = [];

    public function __construct(Environment $env)
    {
        parent::__construct($env);

        $this->source = $this->getSourceContext();

        $this->parent = false;

        $this->blocks = [
        ];
    }

    protected function doDisplay(array $context, array $blocks = [])
    {
        $macros = $this->macros;
        // line 1
        yield "<div id=\"div_view_options\" class=\"container-fluid\">
  <h2>";
yield _gettext("Display chart");
        // line 2
        yield "</h2>

  <div class=\"card\">
    <div class=\"card-body\">
      <form method=\"post\" id=\"tblchartform\" action=\"";
        // line 6
        yield PhpMyAdmin\Url::getFromRoute("/table/chart");
        yield "\" class=\"ajax\">
        ";
        // line 7
        yield PhpMyAdmin\Url::getHiddenInputs(($context["url_params"] ?? null));
        yield "

        <fieldset class=\"mb-3\" role=\"radiogroup\">
          <legend class=\"visually-hidden\">";
yield _gettext("Chart type");
        // line 10
        yield "</legend>
          <div class=\"form-check form-check-inline\">
            <input class=\"form-check-input\" type=\"radio\" name=\"chartType\" value=\"bar\" id=\"barChartTypeRadio\">
            <label class=\"form-check-label\" for=\"barChartTypeRadio\">";
yield _pgettext("Chart type", "Bar");
        // line 13
        yield "</label>
          </div>
          <div class=\"form-check form-check-inline\">
            <input class=\"form-check-input\" type=\"radio\" name=\"chartType\" value=\"column\" id=\"columnChartTypeRadio\">
            <label class=\"form-check-label\" for=\"columnChartTypeRadio\">";
yield _pgettext("Chart type", "Column");
        // line 17
        yield "</label>
          </div>
          <div class=\"form-check form-check-inline\">
            <input class=\"form-check-input\" type=\"radio\" name=\"chartType\" value=\"line\" id=\"lineChartTypeRadio\" checked>
            <label class=\"form-check-label\" for=\"lineChartTypeRadio\">";
yield _pgettext("Chart type", "Line");
        // line 21
        yield "</label>
          </div>
          <div class=\"form-check form-check-inline\">
            <input class=\"form-check-input\" type=\"radio\" name=\"chartType\" value=\"spline\" id=\"splineChartTypeRadio\">
            <label class=\"form-check-label\" for=\"splineChartTypeRadio\">";
yield _pgettext("Chart type", "Spline");
        // line 25
        yield "</label>
          </div>
          <div class=\"form-check form-check-inline\">
            <input class=\"form-check-input\" type=\"radio\" name=\"chartType\" value=\"area\" id=\"areaChartTypeRadio\">
            <label class=\"form-check-label\" for=\"areaChartTypeRadio\">";
yield _pgettext("Chart type", "Area");
        // line 29
        yield "</label>
          </div>
          <div class=\"form-check form-check-inline d-none\" id=\"pieChartType\">
            <input class=\"form-check-input\" type=\"radio\" name=\"chartType\" value=\"pie\" id=\"pieChartTypeRadio\">
            <label class=\"form-check-label\" for=\"pieChartTypeRadio\">";
yield _pgettext("Chart type", "Pie");
        // line 33
        yield "</label>
          </div>
          <div class=\"form-check form-check-inline d-none\" id=\"timelineChartType\">
            <input class=\"form-check-input\" type=\"radio\" name=\"chartType\" value=\"timeline\" id=\"timelineChartTypeRadio\">
            <label class=\"form-check-label\" for=\"timelineChartTypeRadio\">";
yield _pgettext("Chart type", "Timeline");
        // line 37
        yield "</label>
          </div>
          <div class=\"form-check form-check-inline d-none\" id=\"scatterChartType\">
            <input class=\"form-check-input\" type=\"radio\" name=\"chartType\" value=\"scatter\" id=\"scatterChartTypeRadio\">
            <label class=\"form-check-label\" for=\"scatterChartTypeRadio\">";
yield _pgettext("Chart type", "Scatter");
        // line 41
        yield "</label>
          </div>
        </fieldset>

        <div class=\"form-check mb-3 d-none\" id=\"barStacked\">
          <input class=\"form-check-input\" type=\"checkbox\" name=\"barStackedCheckbox\" value=\"1\" id=\"barStackedCheckbox\">
          <label class=\"form-check-label\" for=\"barStackedCheckbox\">";
yield _gettext("Stacked");
        // line 47
        yield "</label>
        </div>

        <div class=\"mb-3\">
          <label class=\"form-label\" for=\"chartTitleInput\">";
yield _gettext("Chart title:");
        // line 51
        yield "</label>
          <input class=\"form-control\" type=\"text\" name=\"chartTitleInput\" id=\"chartTitleInput\">
        </div>

        ";
        // line 55
        $context["xaxis"] = null;
        // line 56
        yield "        <div class=\"mb-3\">
          <label class=\"form-label\" for=\"chartXAxisSelect\">";
yield _gettext("X-Axis:");
        // line 57
        yield "</label>
          <select class=\"form-select\" name=\"chartXAxisSelect\" id=\"chartXAxisSelect\">
            ";
        // line 59
        $context['_parent'] = $context;
        $context['_seq'] = CoreExtension::ensureTraversable(($context["keys"] ?? null));
        foreach ($context['_seq'] as $context["idx"] => $context["key"]) {
            // line 60
            yield "              ";
            if ((($context["xaxis"] ?? null) === null)) {
                // line 61
                yield "                ";
                $context["xaxis"] = $context["idx"];
                // line 62
                yield "              ";
            }
            // line 63
            yield "              ";
            if ((($context["xaxis"] ?? null) === $context["idx"])) {
                // line 64
                yield "                <option value=\"";
                yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($context["idx"], "html", null, true);
                yield "\" selected>";
                yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($context["key"], "html", null, true);
                yield "</option>
              ";
            } else {
                // line 66
                yield "                <option value=\"";
                yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($context["idx"], "html", null, true);
                yield "\">";
                yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($context["key"], "html", null, true);
                yield "</option>
              ";
            }
            // line 68
            yield "            ";
        }
        $_parent = $context['_parent'];
        unset($context['_seq'], $context['_iterated'], $context['idx'], $context['key'], $context['_parent'], $context['loop']);
        $context = array_intersect_key($context, $_parent) + $_parent;
        // line 69
        yield "          </select>
        </div>

        <div class=\"mb-3\">
          <label class=\"form-label\" for=\"chartSeriesSelect\">";
yield _gettext("Series:");
        // line 73
        yield "</label>
          <select class=\"form-select resize-vertical\" name=\"chartSeriesSelect\" id=\"chartSeriesSelect\" multiple>
            ";
        // line 75
        $context['_parent'] = $context;
        $context['_seq'] = CoreExtension::ensureTraversable(($context["keys"] ?? null));
        foreach ($context['_seq'] as $context["idx"] => $context["key"]) {
            // line 76
            yield "              ";
            if (CoreExtension::getAttribute($this->env, $this->source, (($__internal_compile_0 = ($context["fields_meta"] ?? null)) && is_array($__internal_compile_0) || $__internal_compile_0 instanceof ArrayAccess ? ($__internal_compile_0[$context["idx"]] ?? null) : null), "isNumeric", [], "any", false, false, false, 76)) {
                // line 77
                yield "                ";
                if ((($context["idx"] == ($context["xaxis"] ?? null)) && ($context["table_has_a_numeric_column"] ?? null))) {
                    // line 78
                    yield "                  <option value=\"";
                    yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($context["idx"], "html", null, true);
                    yield "\">";
                    yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($context["key"], "html", null, true);
                    yield "</option>
                ";
                } else {
                    // line 80
                    yield "                  <option value=\"";
                    yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($context["idx"], "html", null, true);
                    yield "\" selected>";
                    yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($context["key"], "html", null, true);
                    yield "</option>
                ";
                }
                // line 82
                yield "              ";
            }
            // line 83
            yield "            ";
        }
        $_parent = $context['_parent'];
        unset($context['_seq'], $context['_iterated'], $context['idx'], $context['key'], $context['_parent'], $context['loop']);
        $context = array_intersect_key($context, $_parent) + $_parent;
        // line 84
        yield "          </select>
        </div>

        <input type=\"hidden\" name=\"dateTimeCols\" value=\"";
        // line 88
        $context['_parent'] = $context;
        $context['_seq'] = CoreExtension::ensureTraversable(($context["keys"] ?? null));
        foreach ($context['_seq'] as $context["idx"] => $context["key"]) {
            // line 89
            if (CoreExtension::getAttribute($this->env, $this->source, (($__internal_compile_1 = ($context["fields_meta"] ?? null)) && is_array($__internal_compile_1) || $__internal_compile_1 instanceof ArrayAccess ? ($__internal_compile_1[$context["idx"]] ?? null) : null), "isDateTimeType", [], "method", false, false, false, 89)) {
                // line 90
                yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape(($context["idx"] . " "), "html", null, true);
            }
        }
        $_parent = $context['_parent'];
        unset($context['_seq'], $context['_iterated'], $context['idx'], $context['key'], $context['_parent'], $context['loop']);
        $context = array_intersect_key($context, $_parent) + $_parent;
        // line 92
        yield "\">
        <input type=\"hidden\" name=\"numericCols\" value=\"";
        // line 94
        $context['_parent'] = $context;
        $context['_seq'] = CoreExtension::ensureTraversable(($context["keys"] ?? null));
        foreach ($context['_seq'] as $context["idx"] => $context["key"]) {
            // line 95
            if (CoreExtension::getAttribute($this->env, $this->source, (($__internal_compile_2 = ($context["fields_meta"] ?? null)) && is_array($__internal_compile_2) || $__internal_compile_2 instanceof ArrayAccess ? ($__internal_compile_2[$context["idx"]] ?? null) : null), "isNumeric", [], "any", false, false, false, 95)) {
                // line 96
                yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape(($context["idx"] . " "), "html", null, true);
            }
        }
        $_parent = $context['_parent'];
        unset($context['_seq'], $context['_iterated'], $context['idx'], $context['key'], $context['_parent'], $context['loop']);
        $context = array_intersect_key($context, $_parent) + $_parent;
        // line 98
        yield "\">

        <div class=\"mb-3\">
          <label class=\"form-label\" for=\"xAxisLabelInput\">";
yield _gettext("X-Axis label:");
        // line 101
        yield "</label>
          <input class=\"form-control\" type=\"text\" name=\"xAxisLabelInput\" id=\"xAxisLabelInput\" value=\"";
        // line 102
        yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape((((($context["xaxis"] ?? null) ==  -1)) ? (_gettext("X Values")) : ((($__internal_compile_3 = ($context["keys"] ?? null)) && is_array($__internal_compile_3) || $__internal_compile_3 instanceof ArrayAccess ? ($__internal_compile_3[($context["xaxis"] ?? null)] ?? null) : null))), "html", null, true);
        yield "\">
        </div>

        <div class=\"mb-3\">
          <label class=\"form-label\" for=\"yAxisLabelInput\">";
yield _gettext("Y-Axis label:");
        // line 106
        yield "</label>
          <input class=\"form-control\" type=\"text\" name=\"yAxisLabelInput\" id=\"yAxisLabelInput\" value=\"";
yield _gettext("Y Values");
        // line 107
        yield "\">
        </div>

        <div class=\"form-check mb-3\">
          <input class=\"form-check-input\" type=\"checkbox\" id=\"seriesColumnCheckbox\" name=\"seriesColumnCheckbox\" value=\"1\">
          <label class=\"form-check-label\" for=\"seriesColumnCheckbox\">";
yield _gettext("Series names are in a column");
        // line 112
        yield "</label>
        </div>

        <div class=\"mb-3\">
          <label class=\"form-label\" for=\"chartSeriesColumnSelect\">";
yield _gettext("Series column:");
        // line 116
        yield "</label>
          <select class=\"form-select\" name=\"chartSeriesColumnSelect\" id=\"chartSeriesColumnSelect\" disabled>
            ";
        // line 118
        $context['_parent'] = $context;
        $context['_seq'] = CoreExtension::ensureTraversable(($context["keys"] ?? null));
        foreach ($context['_seq'] as $context["idx"] => $context["key"]) {
            // line 119
            yield "              <option value=\"";
            yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($context["idx"], "html", null, true);
            yield "\"";
            yield ((($context["idx"] == 1)) ? (" selected") : (""));
            yield ">";
            yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($context["key"], "html", null, true);
            yield "</option>
              ";
            // line 120
            $context["series_column"] = $context["idx"];
            // line 121
            yield "            ";
        }
        $_parent = $context['_parent'];
        unset($context['_seq'], $context['_iterated'], $context['idx'], $context['key'], $context['_parent'], $context['loop']);
        $context = array_intersect_key($context, $_parent) + $_parent;
        // line 122
        yield "          </select>
        </div>

        <div class=\"mb-3\">
          <label class=\"form-label\" for=\"chartValueColumnSelect\">";
yield _gettext("Value Column:");
        // line 126
        yield "</label>
          <select class=\"form-select\" name=\"chartValueColumnSelect\" id=\"chartValueColumnSelect\" disabled>
            ";
        // line 128
        $context["selected"] = false;
        // line 129
        yield "            ";
        $context['_parent'] = $context;
        $context['_seq'] = CoreExtension::ensureTraversable(($context["keys"] ?? null));
        foreach ($context['_seq'] as $context["idx"] => $context["key"]) {
            // line 130
            yield "              ";
            if (CoreExtension::getAttribute($this->env, $this->source, (($__internal_compile_4 = ($context["fields_meta"] ?? null)) && is_array($__internal_compile_4) || $__internal_compile_4 instanceof ArrayAccess ? ($__internal_compile_4[$context["idx"]] ?? null) : null), "isNumeric", [], "any", false, false, false, 130)) {
                // line 131
                yield "                ";
                if ((( !($context["selected"] ?? null) && ($context["idx"] != ($context["xaxis"] ?? null))) && ($context["idx"] != ($context["series_column"] ?? null)))) {
                    // line 132
                    yield "                  <option value=\"";
                    yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($context["idx"], "html", null, true);
                    yield "\" selected>";
                    yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($context["key"], "html", null, true);
                    yield "</option>
                  ";
                    // line 133
                    $context["selected"] = true;
                    // line 134
                    yield "                ";
                } else {
                    // line 135
                    yield "                  <option value=\"";
                    yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($context["idx"], "html", null, true);
                    yield "\">";
                    yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape($context["key"], "html", null, true);
                    yield "</option>
                ";
                }
                // line 137
                yield "              ";
            }
            // line 138
            yield "            ";
        }
        $_parent = $context['_parent'];
        unset($context['_seq'], $context['_iterated'], $context['idx'], $context['key'], $context['_parent'], $context['loop']);
        $context = array_intersect_key($context, $_parent) + $_parent;
        // line 139
        yield "          </select>
        </div>

        ";
        // line 142
        yield Twig\Extension\CoreExtension::include($this->env, $context, "table/start_and_number_of_rows_fieldset.twig", ($context["start_and_number_of_rows_fieldset"] ?? null));
        yield "

        <div id=\"resizer\">
          <div class=\"position-absolute top-0 end-0 mt-1 me-1\">
            <a class=\"disableAjax\" id=\"saveChart\" href=\"#\" download=\"chart.png\">
              ";
        // line 147
        yield PhpMyAdmin\Html\Generator::getImage("b_saveimage", _gettext("Save chart as image"));
        yield "
            </a>
          </div>
          <div id=\"querychart\" dir=\"ltr\"></div>
        </div>
      </form>
    </div>
  </div>
</div>
";
        return; yield '';
    }

    /**
     * @codeCoverageIgnore
     */
    public function getTemplateName()
    {
        return "table/chart/tbl_chart.twig";
    }

    /**
     * @codeCoverageIgnore
     */
    public function isTraitable()
    {
        return false;
    }

    /**
     * @codeCoverageIgnore
     */
    public function getDebugInfo()
    {
        return array (  391 => 147,  383 => 142,  378 => 139,  372 => 138,  369 => 137,  361 => 135,  358 => 134,  356 => 133,  349 => 132,  346 => 131,  343 => 130,  338 => 129,  336 => 128,  332 => 126,  325 => 122,  319 => 121,  317 => 120,  308 => 119,  304 => 118,  300 => 116,  293 => 112,  285 => 107,  281 => 106,  273 => 102,  270 => 101,  264 => 98,  257 => 96,  255 => 95,  251 => 94,  248 => 92,  241 => 90,  239 => 89,  235 => 88,  230 => 84,  224 => 83,  221 => 82,  213 => 80,  205 => 78,  202 => 77,  199 => 76,  195 => 75,  191 => 73,  184 => 69,  178 => 68,  170 => 66,  162 => 64,  159 => 63,  156 => 62,  153 => 61,  150 => 60,  146 => 59,  142 => 57,  138 => 56,  136 => 55,  130 => 51,  123 => 47,  114 => 41,  107 => 37,  100 => 33,  93 => 29,  86 => 25,  79 => 21,  72 => 17,  65 => 13,  59 => 10,  52 => 7,  48 => 6,  42 => 2,  38 => 1,);
    }

    public function getSourceContext()
    {
        return new Source("", "table/chart/tbl_chart.twig", "/Users/halid/Desktop/Trollflix/backend/phpmyadmin/templates/table/chart/tbl_chart.twig");
    }
}
