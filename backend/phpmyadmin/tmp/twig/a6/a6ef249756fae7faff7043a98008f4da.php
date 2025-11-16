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

/* table/start_and_number_of_rows_fieldset.twig */
class __TwigTemplate_49e3c1197c11871271254850f5206797 extends Template
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
        yield "<fieldset class=\"row g-3 align-items-center my-3\">
  <div class=\"col-auto\">
    <label class=\"col-form-label\" for=\"startRowInput\">";
yield _gettext("Start row:");
        // line 3
        yield "</label>
  </div>
  <div class=\"col-auto\">
    <input class=\"form-control\" id=\"startRowInput\" type=\"number\" name=\"pos\" min=\"0\" value=\"";
        // line 6
        yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape(($context["pos"] ?? null), "html", null, true);
        yield "\"";
        if ((($context["unlim_num_rows"] ?? null) > 0)) {
            yield " max=\"";
            yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape((($context["unlim_num_rows"] ?? null) - 1), "html", null, true);
            yield "\"";
        }
        yield " required>
  </div>
  <div class=\"col-auto\">
    <label class=\"col-form-label\" for=\"maxRowsInput\">";
yield _gettext("Number of rows:");
        // line 9
        yield "</label>
  </div>
  <div class=\"col-auto\">
    <input class=\"form-control\" id=\"maxRowsInput\" type=\"number\" name=\"session_max_rows\" min=\"1\" value=\"";
        // line 12
        yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape(($context["rows"] ?? null), "html", null, true);
        yield "\" required>
  </div>
  <div class=\"col-auto\">
    <input class=\"btn btn-primary\" type=\"submit\" name=\"submit\" value=\"";
yield _gettext("Go");
        // line 15
        yield "\">
  </div>
  <input type=\"hidden\" name=\"sql_query\" value=\"";
        // line 17
        yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape(($context["sql_query"] ?? null), "html", null, true);
        yield "\">
  <input type=\"hidden\" name=\"unlim_num_rows\" value=\"";
        // line 18
        yield $this->env->getRuntime('Twig\Runtime\EscaperRuntime')->escape(($context["unlim_num_rows"] ?? null), "html", null, true);
        yield "\">
</fieldset>
";
        return; yield '';
    }

    /**
     * @codeCoverageIgnore
     */
    public function getTemplateName()
    {
        return "table/start_and_number_of_rows_fieldset.twig";
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
        return array (  81 => 18,  77 => 17,  73 => 15,  66 => 12,  61 => 9,  48 => 6,  43 => 3,  38 => 1,);
    }

    public function getSourceContext()
    {
        return new Source("", "table/start_and_number_of_rows_fieldset.twig", "/Users/halid/Desktop/Trollflix/backend/phpmyadmin/templates/table/start_and_number_of_rows_fieldset.twig");
    }
}
